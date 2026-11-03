"""
CONCODE Neural Brain -- Sandboxed Runtime Executor

Provides isolated, capability-gated execution of workspace code and test suites
inside temporary directories with sanitized environment variables, strict timeouts,
and bounded output capture.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("concode.sandbox")


@dataclass
class SandboxPolicy:
    """Capability and resource limits for sandboxed execution."""

    allow_execution: bool = False
    timeout_seconds: float = 5.0
    max_output_bytes: int = 32_768
    allowed_languages: Tuple[str, ...] = ("python", "javascript")


@dataclass
class SandboxResult:
    """Structured result from a sandboxed code or test run."""

    target: str
    language: str
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool
    passed: bool
    duration_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SandboxedExecutor:
    """
    Executes scripts or unit tests inside an ephemeral temporary directory
    with a stripped environment and deterministic timeout enforcement.
    """

    def __init__(self, policy: Optional[SandboxPolicy] = None):
        self.policy = policy or SandboxPolicy()

    def run_snippet(
        self,
        code: str,
        language: str = "python",
        workspace_files: Optional[Dict[str, str]] = None,
    ) -> SandboxResult:
        """Execute a standalone snippet in an isolated temporary directory."""
        lang = language.lower().strip()
        if lang in ("py", "python3"):
            lang = "python"
        elif lang in ("js", "node", "nodejs"):
            lang = "javascript"

        if not self.policy.allow_execution:
            return SandboxResult(
                target="snippet",
                language=lang,
                exit_code=-1,
                stdout="",
                stderr="Sandbox execution is disabled by policy (allow_execution=False).",
                timed_out=False,
                passed=False,
                duration_ms=0.0,
            )

        if lang not in self.policy.allowed_languages:
            return SandboxResult(
                target="snippet",
                language=lang,
                exit_code=-1,
                stdout="",
                stderr=f"Language '{lang}' is not permitted by sandbox policy.",
                timed_out=False,
                passed=False,
                duration_ms=0.0,
            )

        files = dict(workspace_files or {})
        entry_file = "_sandbox_entry.py" if lang == "python" else "_sandbox_entry.js"
        files[entry_file] = code
        return self._execute_in_tempdir(files, entry_file, lang)

    def verify_workspace_tests(
        self, workspace_files: Dict[str, str]
    ) -> List[SandboxResult]:
        """
        Discover and run any test files (`test_*.py`, `*_test.py`, `*.test.js`)
        in the supplied workspace snapshot when execution is enabled.
        """
        if not self.policy.allow_execution:
            return []

        results: List[SandboxResult] = []
        for path in sorted(workspace_files.keys()):
            name = PurePosixPath(path).name.lower()
            if name.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py")):
                results.append(
                    self._execute_in_tempdir(workspace_files, path, "python", run_unittest=True)
                )
            elif name.endswith(".js") and (name.startswith("test_") or ".test." in name):
                results.append(
                    self._execute_in_tempdir(workspace_files, path, "javascript")
                )
        return results

    def _execute_in_tempdir(
        self,
        workspace_files: Dict[str, str],
        target_rel_path: str,
        language: str,
        run_unittest: bool = False,
    ) -> SandboxResult:
        start = time.time()
        with tempfile.TemporaryDirectory(prefix="concode-sandbox-") as tmp_dir:
            # Materialize workspace files safely
            for rel_path, content in workspace_files.items():
                if not self._is_safe_path(rel_path):
                    continue
                full_path = os.path.join(tmp_dir, rel_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as handle:
                    handle.write(content)

            cmd = self._build_command(language, target_rel_path, run_unittest)
            if not cmd:
                return SandboxResult(
                    target=target_rel_path,
                    language=language,
                    exit_code=127,
                    stdout="",
                    stderr=f"Runtime binary for '{language}' is not installed on host.",
                    timed_out=False,
                    passed=False,
                    duration_ms=round((time.time() - start) * 1000, 2),
                )

            sanitized_env = {
                "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "HOME": tmp_dir,
                "TMPDIR": tmp_dir,
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONUNBUFFERED": "1",
                "PYTHONNOUSERSITE": "1",
                "TOKENIZERS_PARALLELISM": "false",
                "NO_COLOR": "1",
                "PYTHONPATH": tmp_dir,
            }

            try:
                proc = subprocess.run(
                    cmd,
                    cwd=tmp_dir,
                    env=sanitized_env,
                    capture_output=True,
                    timeout=self.policy.timeout_seconds,
                    check=False,
                )
                duration_ms = round((time.time() - start) * 1000, 2)
                stdout = self._truncate(proc.stdout)
                stderr = self._truncate(proc.stderr)
                return SandboxResult(
                    target=target_rel_path,
                    language=language,
                    exit_code=proc.returncode,
                    stdout=stdout,
                    stderr=stderr,
                    timed_out=False,
                    passed=(proc.returncode == 0),
                    duration_ms=duration_ms,
                )
            except subprocess.TimeoutExpired as exc:
                duration_ms = round((time.time() - start) * 1000, 2)
                return SandboxResult(
                    target=target_rel_path,
                    language=language,
                    exit_code=124,
                    stdout=self._truncate(exc.stdout or b""),
                    stderr=f"Execution timed out after {self.policy.timeout_seconds}s.",
                    timed_out=True,
                    passed=False,
                    duration_ms=duration_ms,
                )

    @staticmethod
    def _build_command(language: str, target_rel_path: str, run_unittest: bool) -> Optional[List[str]]:
        if language == "python":
            py_bin = sys.executable or shutil.which("python3")
            if not py_bin:
                return None
            if run_unittest:
                return [py_bin, "-B", "-s", "-m", "unittest", target_rel_path]
            return [py_bin, "-B", "-s", target_rel_path]
        if language == "javascript":
            node_bin = shutil.which("node")
            if not node_bin:
                return None
            return [node_bin, target_rel_path]
        return None

    def _truncate(self, raw: bytes | str) -> str:
        if isinstance(raw, bytes):
            raw_bytes = raw[: self.policy.max_output_bytes]
            return raw_bytes.decode("utf-8", errors="replace")
        return raw[: self.policy.max_output_bytes]

    @staticmethod
    def _is_safe_path(path: str) -> bool:
        if not path or "\x00" in path or "\\" in path:
            return False
        candidate = PurePosixPath(path)
        return not candidate.is_absolute() and ".." not in candidate.parts and str(candidate) != "."
