---
title: Security Protocol -- API Key Validation
type: security_protocol
tags:
  - protocol/api-key
  - security/auth
---

# Security Protocol: API Key Validation

> Header-based API key authentication middleware restricting cognitive endpoint access to authorized clients.

---

## Validation Sequence

1. Extracts `X-API-Key` header from every incoming request to protected endpoints.
2. Compares the key against the server-side secret loaded from environment variable `CONCODE_API_KEY`.
3. Rejects with `HTTP 401 Unauthorized` if the key is missing or does not match.

---

## Implementation Reference

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(key: str = Security(api_key_header)):
    if key != os.environ.get("CONCODE_API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
```

---

## Key Management

- Store the key in `.env` (never commit to version control).
- Rotate the key on any suspected compromise.
- Support multiple keys for different client applications via a key registry.

---

## Related Notes

- MOC: [[11-Security-Protocols/Security-Protocols-MOC|Security-Protocols-MOC]]
- Subsystem: [[01-Brain-Architecture/06-FastAPI-Service|06-FastAPI-Service]]
- Protocol: [[11-Security-Protocols/01-JWT-Token-Verification|01-JWT-Token-Verification]]
