"""
CONCODE Neural Brain -- Security Layer

Implements all 4 security protocols documented in the vault:
  1. API Key Validation (X-API-Key header, constant-time comparison)
  2. Rate Limiting (sliding window per-IP throttling)
  3. Input Sanitization (null bytes, ANSI escapes, path traversal)
  4. Security Headers (X-Content-Type-Options, X-Frame-Options, X-Request-ID)
"""

import hashlib
import hmac
import logging
import os
import re
import time
import uuid
from collections import defaultdict
from typing import Callable, Dict, Optional, Tuple

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("concode.security")


# =====================================================================
#  SEC 1 -- API Key Authentication
# =====================================================================

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _get_configured_api_key() -> Optional[str]:
    """Load the API key from environment. Returns None if not configured."""
    return os.environ.get("CONCODE_API_KEY")


async def verify_api_key(
    api_key: Optional[str] = Security(_api_key_header),
) -> Optional[str]:
    """
    FastAPI dependency that verifies the X-API-Key header.

    Behavior:
    - If CONCODE_API_KEY env var is NOT set -> dev mode, all requests pass.
    - If CONCODE_API_KEY env var IS set -> production mode, key is required.
    - Uses constant-time comparison to prevent timing attacks.

    Returns:
        The validated API key string, or None in dev mode.
    """
    configured_key = _get_configured_api_key()

    # Dev mode: no key configured, skip auth entirely
    if configured_key is None:
        return None

    # Production mode: key is required
    if api_key is None:
        logger.warning("Request rejected: missing X-API-Key header")
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Provide X-API-Key header.",
        )

    # Constant-time comparison to prevent timing side-channel attacks
    key_valid = hmac.compare_digest(
        api_key.encode("utf-8"),
        configured_key.encode("utf-8"),
    )

    if not key_valid:
        logger.warning("Request rejected: invalid API key")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key.",
        )

    return api_key


# =====================================================================
#  SEC 2 -- Rate Limiting (Sliding Window Counter)
# =====================================================================

class RateLimiter:
    """
    In-memory sliding window rate limiter.

    Tracks request timestamps per client key (IP address) and enforces
    a maximum number of requests within a rolling time window.
    Auto-prunes stale entries to prevent memory growth.
    """

    def __init__(
        self,
        max_requests: int = 30,
        window_seconds: int = 60,
        cleanup_interval: int = 300,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.cleanup_interval = cleanup_interval
        self._requests: Dict[str, list] = defaultdict(list)
        self._last_cleanup = time.time()

    def is_allowed(self, client_key: str) -> Tuple[bool, int, int]:
        """
        Check if a request from client_key is allowed.

        Returns:
            (allowed, remaining_requests, retry_after_seconds)
        """
        now = time.time()
        window_start = now - self.window_seconds

        # Prune old timestamps for this client
        timestamps = self._requests[client_key]
        self._requests[client_key] = [
            ts for ts in timestamps if ts > window_start
        ]
        timestamps = self._requests[client_key]

        # Periodic global cleanup of stale client entries
        if now - self._last_cleanup > self.cleanup_interval:
            self._cleanup_stale(now)

        remaining = self.max_requests - len(timestamps)

        if len(timestamps) >= self.max_requests:
            # Calculate retry-after from oldest request in window
            oldest = min(timestamps) if timestamps else now
            retry_after = int(self.window_seconds - (now - oldest)) + 1
            return False, 0, max(retry_after, 1)

        # Record this request
        self._requests[client_key].append(now)
        return True, max(remaining - 1, 0), 0

    def _cleanup_stale(self, now: float) -> None:
        """Remove client entries with no recent requests."""
        window_start = now - self.window_seconds
        stale_keys = [
            key for key, timestamps in self._requests.items()
            if not timestamps or max(timestamps) < window_start
        ]
        for key in stale_keys:
            del self._requests[key]
        self._last_cleanup = now
        if stale_keys:
            logger.debug(f"Rate limiter: pruned {len(stale_keys)} stale IP entries")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that enforces per-IP rate limits.

    Tiered limits:
    - /api/v1/cognitive (GPU-bound): 30 req/min
    - All other endpoints: 120 req/min
    """

    def __init__(self, app, cognitive_limit: int = 30, general_limit: int = 120):
        super().__init__(app)
        self.cognitive_limiter = RateLimiter(
            max_requests=cognitive_limit, window_seconds=60
        )
        self.general_limiter = RateLimiter(
            max_requests=general_limit, window_seconds=60
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = _get_client_ip(request)

        # Select the appropriate limiter based on path
        path = request.url.path
        if path.startswith(("/api/v1/cognitive", "/api/v1/agent", "/api/v1/travel")):
            limiter = self.cognitive_limiter
        elif path.startswith("/api/"):
            limiter = self.general_limiter
        else:
            # Static/health endpoints are not rate limited
            return await call_next(request)

        allowed, remaining, retry_after = limiter.is_allowed(client_ip)

        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {client_ip} on {path} "
                f"(retry after {retry_after}s)"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Slow down.",
                    "retry_after": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limiter.max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response


# =====================================================================
#  SEC 3 -- Input Sanitization
# =====================================================================

# Patterns for stripping dangerous content
_NULL_BYTES_RE = re.compile(r"[\x00]")
_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
_CONTROL_CHARS_RE = re.compile(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_input(text: str) -> str:
    """
    Sanitize user-provided text input.

    - Strips null bytes (prevents C-string truncation attacks)
    - Strips ANSI escape sequences (prevents terminal injection)
    - Strips other control characters
    - Trims leading/trailing whitespace
    """
    text = _NULL_BYTES_RE.sub("", text)
    text = _ANSI_ESCAPE_RE.sub("", text)
    text = _CONTROL_CHARS_RE.sub("", text)
    return text.strip()


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a workspace filename to prevent path traversal.

    - Strips directory traversal components (../)
    - Strips leading slashes
    - Strips null bytes
    - Collapses to basename if suspicious patterns remain
    """
    # Remove null bytes
    filename = _NULL_BYTES_RE.sub("", filename)

    # Remove ANSI escapes
    filename = _ANSI_ESCAPE_RE.sub("", filename)

    # Normalize separators
    filename = filename.replace("\\", "/")

    # Strip leading slashes and dots
    filename = filename.lstrip("/")

    # Remove directory traversal
    while "../" in filename:
        filename = filename.replace("../", "")
    while "..\\" in filename:
        filename = filename.replace("..\\", "")

    # If still suspicious, collapse to basename only
    if "/" in filename and filename.startswith(("etc", "proc", "dev", "sys", "var", "tmp")):
        filename = filename.rsplit("/", 1)[-1]

    # Final safety: strip any remaining leading dots/slashes
    filename = filename.lstrip("./")

    if not filename:
        filename = "untitled"

    return filename


def validate_workspace_files(
    workspace_files: Dict[str, str],
    max_files: int = 50,
    max_file_size: int = 500_000,
    max_total_size: int = 5_000_000,
) -> Dict[str, str]:
    """
    Validate and sanitize workspace file submissions.

    Returns sanitized dict with safe filenames and bounded content.
    Raises HTTPException on violations.
    """
    if len(workspace_files) > max_files:
        raise HTTPException(
            status_code=413,
            detail=f"Too many workspace files. Maximum is {max_files}.",
        )

    sanitized = {}
    total_size = 0

    for raw_name, content in workspace_files.items():
        safe_name = sanitize_filename(raw_name)

        if len(content) > max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File '{safe_name}' exceeds maximum size of {max_file_size} bytes.",
            )

        total_size += len(content)
        if total_size > max_total_size:
            raise HTTPException(
                status_code=413,
                detail=f"Total workspace size exceeds maximum of {max_total_size} bytes.",
            )

        sanitized[safe_name] = content

    return sanitized


# =====================================================================
#  SEC 4 -- Security Response Headers
# =====================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers and request IDs to all responses.

    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-Request-ID: unique UUID per request
    - Cache-Control: no-store (for API responses)
    - Referrer-Policy: strict-origin-when-cross-origin
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Request-ID"] = request_id
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Cache control for API endpoints
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"

        return response


# =====================================================================
#  Utility Functions
# =====================================================================

def _get_client_ip(request: Request) -> str:
    """
    Extract the client IP address from a request.
    Checks X-Forwarded-For header first (for reverse proxy setups),
    then falls back to the direct client address.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain (original client)
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
