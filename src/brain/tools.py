"""
CONCODE Neural Brain -- Universal Tool Bus & MCP Bridge

Provides capability-gated tools for workspace inspection, AST symbol extraction,
safe mathematical computation, Obsidian vault knowledge queries, sandboxed code
execution, and dynamic Model Context Protocol (MCP) tool registration.
"""

from __future__ import annotations

import ast
import ipaddress
import logging
import math
import operator
import os
import re
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Dict, List, Optional, Set
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from src.brain.sandbox import SandboxPolicy, SandboxedExecutor

logger = logging.getLogger("concode.tools")

# Capability permission tiers
PERM_READ_ONLY = "READ_ONLY"
PERM_SANDBOX_EXEC = "SANDBOX_EXEC"
PERM_WORKSPACE_WRITE = "WORKSPACE_WRITE"
PERM_EXTERNAL_NETWORK = "EXTERNAL_NETWORK"
PERM_HUMAN_APPROVAL = "HUMAN_APPROVAL"


@dataclass
class ToolDefinition:
    """Metadata and handler for a registered tool on the Universal Tool Bus."""

    name: str
    description: str
    permission: str
    parameters_schema: Dict[str, Any]
    handler: Callable[..., Dict[str, Any]]
    source: str = "builtin"


@dataclass
class ToolCallResult:
    """Outcome of invoking a tool on the Universal Tool Bus."""

    tool_name: str
    success: bool
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    permission_used: str = PERM_READ_ONLY

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Safe mathematical AST operators and functions
_SAFE_MATH_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_SAFE_MATH_FUNCS: Dict[str, Any] = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "exp": math.exp,
    "ceil": math.ceil,
    "floor": math.floor,
    "factorial": math.factorial,
    "gcd": math.gcd,
    "comb": getattr(math, "comb", None),
    "perm": getattr(math, "perm", None),
    "pi": math.pi,
    "e": math.e,
}


def _eval_math_node(node: ast.AST) -> float | int:
    if isinstance(node, ast.Expression):
        return _eval_math_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Name):
        val = _SAFE_MATH_FUNCS.get(node.id)
        if isinstance(val, (int, float)):
            return val
        raise ValueError(f"Unknown mathematical constant: {node.id}")
    if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_MATH_OPS:
        return _SAFE_MATH_OPS[type(node.op)](_eval_math_node(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_MATH_OPS:
        left = _eval_math_node(node.left)
        right = _eval_math_node(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 1000:
            raise ValueError("Exponent magnitude exceeds safety limit (1000).")
        return _SAFE_MATH_OPS[type(node.op)](left, right)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        fn = _SAFE_MATH_FUNCS.get(node.func.id)
        if not callable(fn):
            raise ValueError(f"Unsupported mathematical function: {node.func.id}")
        args = [_eval_math_node(arg) for arg in node.args]
        if node.func.id == "factorial" and args and args[0] > 500:
            raise ValueError("Factorial argument exceeds safety limit (500).")
        return fn(*args)
    raise ValueError(f"Unsupported syntax in mathematical expression: {ast.dump(node)}")


class UniversalToolBus:
    """
    Capability-gated tool registry and execution bus supporting built-in tools
    and external Model Context Protocol (MCP) tool adapters.
    """

    def __init__(
        self,
        vault_dir: Optional[Path] = None,
        sandbox_executor: Optional[SandboxedExecutor] = None,
        granted_permissions: Optional[Set[str]] = None,
    ):
        self.vault_dir = vault_dir or (Path(__file__).resolve().parent.parent.parent / "concode-neural-brain")
        self.sandbox = sandbox_executor or SandboxedExecutor(SandboxPolicy(allow_execution=False))
        self.granted_permissions: Set[str] = granted_permissions or {PERM_READ_ONLY}
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_builtin_tools()

    def _register_builtin_tools(self) -> None:
        self.register_tool(
            ToolDefinition(
                name="workspace_search",
                description="Search workspace files by regex or substring and return matching lines.",
                permission=PERM_READ_ONLY,
                parameters_schema={"pattern": "str", "workspace_files": "dict"},
                handler=self._tool_workspace_search,
            )
        )
        self.register_tool(
            ToolDefinition(
                name="ast_inspect",
                description="Extract classes, functions, imports, and structural metrics from workspace files.",
                permission=PERM_READ_ONLY,
                parameters_schema={"workspace_files": "dict"},
                handler=self._tool_ast_inspect,
            )
        )
        self.register_tool(
            ToolDefinition(
                name="math_evaluate",
                description="Evaluate deterministic mathematical expressions safely via AST parsing.",
                permission=PERM_READ_ONLY,
                parameters_schema={"expression": "str"},
                handler=self._tool_math_evaluate,
            )
        )
        self.register_tool(
            ToolDefinition(
                name="vault_query",
                description="Search the CONCODE Obsidian knowledge vault for architectural notes and thinking skills.",
                permission=PERM_READ_ONLY,
                parameters_schema={"query": "str", "top_k": "int"},
                handler=self._tool_vault_query,
            )
        )
        self.register_tool(
            ToolDefinition(
                name="sandbox_run",
                description="Execute a Python or JavaScript snippet inside the isolated sandbox runtime.",
                permission=PERM_SANDBOX_EXEC,
                parameters_schema={"code": "str", "language": "str", "workspace_files": "dict"},
                handler=self._tool_sandbox_run,
            )
        )
        self.register_tool(
            ToolDefinition(
                name="git_status_diff",
                description="Inspect git branch, status, and diff summary of a local repository.",
                permission=PERM_READ_ONLY,
                parameters_schema={"repo_dir": "str"},
                handler=self._tool_git_status_diff,
            )
        )
        self.register_tool(
            ToolDefinition(
                name="web_fetch",
                description="Fetch external HTTPS documentation or API JSON with SSRF protection.",
                permission=PERM_EXTERNAL_NETWORK,
                parameters_schema={"url": "str", "timeout": "int"},
                handler=self._tool_web_fetch,
            )
        )
        self.register_tool(
            ToolDefinition(
                name="filesystem_transaction",
                description="Atomically write verified relative files inside an authorized target directory with rollback.",
                permission=PERM_WORKSPACE_WRITE,
                parameters_schema={"target_dir": "str", "files": "dict"},
                handler=self._tool_filesystem_transaction,
            )
        )

    def register_tool(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def register_mcp_tool(
        self,
        server_name: str,
        tool_name: str,
        description: str,
        handler: Callable[..., Dict[str, Any]],
        permission: str = PERM_EXTERNAL_NETWORK,
        parameters_schema: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Register an external MCP tool onto the Universal Tool Bus."""
        qualified_name = f"mcp.{server_name}.{tool_name}"
        self.register_tool(
            ToolDefinition(
                name=qualified_name,
                description=description,
                permission=permission,
                parameters_schema=parameters_schema or {},
                handler=handler,
                source=f"mcp:{server_name}",
            )
        )
        return qualified_name

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "permission": t.permission,
                "source": t.source,
                "enabled": t.permission in self.granted_permissions,
            }
            for t in self._tools.values()
        ]

    def invoke(self, tool_name: str, **kwargs: Any) -> ToolCallResult:
        """Invoke a registered tool if its required capability permission is granted."""
        tool = self._tools.get(tool_name)
        if tool is None:
            return ToolCallResult(
                tool_name=tool_name,
                success=False,
                error=f"Unknown tool: '{tool_name}'",
            )
        if tool.permission not in self.granted_permissions:
            return ToolCallResult(
                tool_name=tool_name,
                success=False,
                error=(
                    f"Permission denied for tool '{tool_name}': requires '{tool.permission}', "
                    f"granted={sorted(self.granted_permissions)}"
                ),
                permission_used=tool.permission,
            )
        try:
            output = tool.handler(**kwargs)
            return ToolCallResult(
                tool_name=tool_name,
                success=True,
                output=output,
                permission_used=tool.permission,
            )
        except Exception as exc:
            logger.warning(f"Tool '{tool_name}' execution error: {exc}")
            return ToolCallResult(
                tool_name=tool_name,
                success=False,
                error=str(exc),
                permission_used=tool.permission,
            )

    @staticmethod
    def _tool_workspace_search(
        pattern: str, workspace_files: Optional[Dict[str, str]] = None, max_matches: int = 30
    ) -> Dict[str, Any]:
        workspace_files = workspace_files or {}
        if not pattern:
            return {"matches": [], "count": 0}
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            regex = re.compile(re.escape(pattern), re.IGNORECASE)

        matches = []
        for path, content in sorted(workspace_files.items()):
            for line_no, line in enumerate(content.splitlines(), start=1):
                if regex.search(line):
                    matches.append({"path": path, "line": line_no, "text": line.strip()[:200]})
                    if len(matches) >= max_matches:
                        return {"matches": matches, "count": len(matches), "truncated": True}
        return {"matches": matches, "count": len(matches), "truncated": False}

    @staticmethod
    def _tool_ast_inspect(workspace_files: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        workspace_files = workspace_files or {}
        summary: Dict[str, Any] = {}
        for path, content in sorted(workspace_files.items()):
            if path.endswith(".py"):
                try:
                    tree = ast.parse(content, filename=path)
                    classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
                    functions = [
                        n.name
                        for n in ast.walk(tree)
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    ]
                    imports = []
                    for n in ast.walk(tree):
                        if isinstance(n, ast.Import):
                            imports.extend(alias.name for alias in n.names)
                        elif isinstance(n, ast.ImportFrom) and n.module:
                            imports.append(n.module)
                    summary[path] = {
                        "language": "python",
                        "classes": classes,
                        "functions": functions,
                        "imports": sorted(set(imports)),
                        "lines": len(content.splitlines()),
                    }
                except SyntaxError as err:
                    summary[path] = {"language": "python", "syntax_error": str(err)}
            else:
                fn_matches = re.findall(
                    r"(?:function\s+([a-zA-Z_$][\w$]*)|const\s+([a-zA-Z_$][\w$]*)\s*=\s*(?:async\s*)?\()",
                    content,
                )
                fns = [m[0] or m[1] for m in fn_matches if (m[0] or m[1])]
                summary[path] = {
                    "language": Path(path).suffix.lstrip(".") or "text",
                    "functions": fns[:50],
                    "lines": len(content.splitlines()),
                }
        return {"files": summary, "total_files": len(summary)}

    @staticmethod
    def _tool_math_evaluate(expression: str) -> Dict[str, Any]:
        cleaned = expression.strip().replace("^", "**")
        parsed = ast.parse(cleaned, mode="eval")
        value = _eval_math_node(parsed)
        return {"expression": expression, "result": value}

    def _tool_vault_query(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        if not self.vault_dir.exists():
            return {"notes": [], "count": 0}
        terms = [t for t in re.findall(r"[a-zA-Z0-9_]{3,}", query.lower())]
        if not terms:
            return {"notes": [], "count": 0}

        scored = []
        for root, _, files in os.walk(self.vault_dir):
            for fname in files:
                if not fname.endswith(".md"):
                    continue
                fpath = Path(root) / fname
                try:
                    text = fpath.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                haystack = f"{fname}\n{text[:3000]}".lower()
                score = sum(haystack.count(term) for term in terms)
                if score > 0:
                    rel = fpath.relative_to(self.vault_dir).as_posix()
                    scored.append((score, rel, text[:600].strip()))

        scored.sort(key=lambda item: item[0], reverse=True)
        top = [
            {"note": rel, "relevance_score": score, "excerpt": excerpt}
            for score, rel, excerpt in scored[: max(1, min(top_k, 10))]
        ]
        return {"notes": top, "count": len(top)}

    def _tool_sandbox_run(
        self,
        code: str,
        language: str = "python",
        workspace_files: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        res = self.sandbox.run_snippet(code=code, language=language, workspace_files=workspace_files)
        return res.to_dict()

    def _tool_git_status_diff(self, repo_dir: Optional[str] = None) -> Dict[str, Any]:
        target = Path(repo_dir).resolve() if repo_dir else self.vault_dir.parent.resolve()
        if not target.exists() or not target.is_dir():
            raise ValueError(f"Repository directory does not exist: {target}")
        status_proc = subprocess.run(
            ["git", "status", "--short", "--branch"],
            cwd=str(target),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        diff_proc = subprocess.run(
            ["git", "diff", "--stat"],
            cwd=str(target),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return {
            "repo_dir": str(target),
            "status": status_proc.stdout.strip()[:4000],
            "diff_stat": diff_proc.stdout.strip()[:4000],
            "exit_code": status_proc.returncode,
        }

    @staticmethod
    def _is_safe_external_url(url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in ("https", "http"):
            return False
        host = (parsed.hostname or "").strip().lower()
        if not host or host in ("localhost", "0.0.0.0", "::1") or host.endswith(".local"):
            return False
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
                return False
        except ValueError:
            pass
        return True

    def _tool_web_fetch(self, url: str, timeout: int = 8, max_bytes: int = 16_384) -> Dict[str, Any]:
        if not self._is_safe_external_url(url):
            raise ValueError(f"Blocked unsafe or private URL target: {url!r}")
        req = Request(url, headers={"User-Agent": "CONCODE-Neural-Brain/3.0"})
        with urlopen(req, timeout=max(1, min(timeout, 20))) as resp:
            raw = resp.read(max_bytes).decode("utf-8", errors="replace")
            content_type = resp.headers.get("Content-Type", "")
            status = getattr(resp, "status", 200)
        if "html" in content_type.lower():
            text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
        else:
            text = raw.strip()
        return {"url": url, "status": status, "content_type": content_type, "content": text[:max_bytes]}

    @staticmethod
    def _tool_filesystem_transaction(target_dir: str, files: Dict[str, str]) -> Dict[str, Any]:
        root = Path(target_dir).resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError(f"Target directory does not exist: {target_dir}")
        if not isinstance(files, dict) or not files:
            raise ValueError("'files' must be a non-empty dictionary of relative_path -> content.")

        backups: Dict[Path, Optional[str]] = {}
        written: List[str] = []
        try:
            for rel_path, content in files.items():
                if not rel_path or "\x00" in rel_path or "\\" in rel_path:
                    raise ValueError(f"Unsafe path in transaction: {rel_path!r}")
                posix = PurePosixPath(rel_path)
                if posix.is_absolute() or ".." in posix.parts or str(posix) == ".":
                    raise ValueError(f"Path traversal rejected in transaction: {rel_path!r}")
                dest = (root / rel_path).resolve()
                if root not in dest.parents and dest != root:
                    raise ValueError(f"Resolved path escapes root directory: {rel_path!r}")

                backups[dest] = dest.read_text(encoding="utf-8") if dest.exists() else None
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(content, encoding="utf-8")
                written.append(rel_path)
            return {"committed": True, "files_written": written, "count": len(written)}
        except Exception:
            # Rollback any partial changes
            for dest, prev in backups.items():
                try:
                    if prev is None:
                        if dest.exists():
                            dest.unlink()
                    else:
                        dest.write_text(prev, encoding="utf-8")
                except Exception:
                    pass
            raise
