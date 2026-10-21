"""Bounded, workspace-snapshot coding agent for CONCODE."""

from __future__ import annotations

import ast
import difflib
import json
import logging
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import PurePosixPath
from typing import Any, Dict, List, Sequence, Tuple

logger = logging.getLogger("concode.agent")


MAX_AGENT_EDITS = 12
MAX_AGENT_FILE_SIZE = 500_000
MAX_CONTEXT_CHARS = 12_000


@dataclass
class AgentEdit:
    """A complete replacement for one workspace file."""

    path: str
    content: str
    reason: str = ""
    previous_content: str = ""

    @property
    def diff(self) -> str:
        return "".join(
            difflib.unified_diff(
                self.previous_content.splitlines(keepends=True),
                self.content.splitlines(keepends=True),
                fromfile=f"a/{self.path}",
                tofile=f"b/{self.path}",
            )
        )


@dataclass
class VerificationResult:
    """Result of a non-executing check over a proposed file change."""

    path: str
    status: str
    detail: str


@dataclass
class AgentOutcome:
    """A portable agent result; changes are never written to the host filesystem."""

    summary: str
    plan: List[str] = field(default_factory=list)
    edits: List[AgentEdit] = field(default_factory=list)
    verification: List[VerificationResult] = field(default_factory=list)
    iterations: int = 0
    success: bool = False
    needs_user_input: bool = False
    question: str | None = None
    error: str | None = None


class _StrictHTMLParser(HTMLParser):
    """Only reports parser errors; HTMLParser remains deliberately permissive."""

    def error(self, message: str) -> None:
        raise ValueError(message)


class CodingAgent:
    """
    Makes bounded coding changes to an in-memory workspace snapshot.

    The agent is intentionally unable to execute user code, run shell commands,
    access the host filesystem, or perform network requests. Callers receive
    complete file replacements and choose whether to apply them to a project.
    """

    def __init__(self, generator: Any):
        self.generator = generator

    def run(
        self,
        goal: str,
        workspace_files: Dict[str, str],
        guild_prompt: str,
        max_iterations: int = 3,
    ) -> AgentOutcome:
        """Plan, edit, verify, and repair a supplied workspace snapshot."""
        workspace = dict(workspace_files)
        max_iterations = max(1, min(max_iterations, 3))
        all_edits: List[AgentEdit] = []
        plan: List[str] = []
        verification: List[VerificationResult] = []
        feedback = ""

        for attempt in range(1, max_iterations + 1):
            prompt = self._build_agent_prompt(
                goal=goal,
                workspace=workspace,
                guild_prompt=guild_prompt,
                feedback=feedback,
            )
            raw_response = self.generator.generate(
                system_prompt=self._system_prompt(guild_prompt),
                user_prompt=prompt,
                context="",
                history=None,
            )
            decision, parse_error = self._parse_decision(raw_response)
            if decision is None:
                decision = self._decision_from_code_snippet(raw_response, workspace, goal)
            if decision is None:
                feedback = (
                    "Your previous response was not valid JSON. "
                    f"Parser error: {parse_error}. Return only the specified JSON object."
                )
                if attempt == max_iterations:
                    return AgentOutcome(
                        summary="The model did not return an applicable change set.",
                        plan=plan,
                        edits=all_edits,
                        verification=verification,
                        iterations=attempt,
                        error=feedback,
                    )
                continue

            plan = self._as_string_list(decision.get("plan"))
            summary = self._as_string(decision.get("summary"), "No summary supplied.")
            if bool(decision.get("needs_user_input")):
                return AgentOutcome(
                    summary=summary,
                    plan=plan,
                    iterations=attempt,
                    needs_user_input=True,
                    question=self._as_string(decision.get("question"), "Please provide more project detail."),
                )

            edits, edit_error = self._validated_edits(decision.get("edits"), workspace)
            if edit_error:
                feedback = f"Your proposed edits were rejected: {edit_error} Return corrected JSON."
                if attempt == max_iterations:
                    return AgentOutcome(
                        summary=summary,
                        plan=plan,
                        edits=all_edits,
                        verification=verification,
                        iterations=attempt,
                        error=feedback,
                    )
                continue

            if not edits:
                return AgentOutcome(
                    summary=summary,
                    plan=plan,
                    iterations=attempt,
                    success=True,
                )

            candidate = dict(workspace)
            for edit in edits:
                candidate[edit.path] = edit.content
            attempt_verification = self.verify(candidate, [edit.path for edit in edits])
            failures = [result for result in attempt_verification if result.status == "failed"]

            if not failures:
                workspace = candidate
                all_edits.extend(edits)
                verification.extend(attempt_verification)
                return AgentOutcome(
                    summary=summary,
                    plan=plan,
                    edits=all_edits,
                    verification=verification,
                    iterations=attempt,
                    success=True,
                )

            failure_text = "; ".join(f"{item.path}: {item.detail}" for item in failures)
            feedback = (
                "Verification failed for your proposed changes. Keep the goal, correct the "
                f"following errors, and return a complete new JSON decision: {failure_text}"
            )
            verification.extend(attempt_verification)

        return AgentOutcome(
            summary="The agent exhausted its verification attempts.",
            plan=plan,
            edits=all_edits,
            verification=verification,
            iterations=max_iterations,
            error=feedback,
        )

    def verify(self, workspace: Dict[str, str], paths: Sequence[str]) -> List[VerificationResult]:
        """Perform deterministic syntax and structure checks without executing code."""
        results: List[VerificationResult] = []
        for path in paths:
            content = workspace[path]
            suffix = PurePosixPath(path).suffix.lower()
            try:
                if suffix == ".py":
                    ast.parse(content, filename=path)
                    results.append(VerificationResult(path, "passed", "Python syntax parsed."))
                elif suffix == ".json":
                    json.loads(content)
                    results.append(VerificationResult(path, "passed", "JSON parsed."))
                elif suffix in {".yaml", ".yml"}:
                    self._verify_yaml(content)
                    results.append(VerificationResult(path, "passed", "YAML parsed."))
                elif suffix in {".js", ".mjs", ".cjs"}:
                    results.append(self._verify_javascript(path, content))
                elif suffix in {".ts", ".tsx", ".jsx", ".css"}:
                    self._verify_balanced_delimiters(content)
                    results.append(VerificationResult(path, "passed", "Delimiters balanced."))
                elif suffix in {".html", ".htm"}:
                    parser = _StrictHTMLParser()
                    parser.feed(content)
                    parser.close()
                    results.append(VerificationResult(path, "passed", "HTML parsed."))
                else:
                    results.append(VerificationResult(path, "skipped", "No safe verifier is configured for this file type."))
            except (SyntaxError, ValueError, json.JSONDecodeError) as error:
                detail = getattr(error, "msg", str(error)) or error.__class__.__name__
                results.append(VerificationResult(path, "failed", str(detail)))
        return results

    @staticmethod
    def _system_prompt(guild_prompt: str) -> str:
        return (
            "You are a careful software-engineering agent. "
            "You work only on an in-memory workspace supplied by the user. "
            "Do not claim to run tests, access files outside the workspace, use the network, "
            "or complete work you cannot verify. "
            f"Specialist guidance: {guild_prompt}"
        )

    def _build_agent_prompt(
        self,
        goal: str,
        workspace: Dict[str, str],
        guild_prompt: str,
        feedback: str,
    ) -> str:
        context = self._workspace_context(goal, workspace)
        retry_note = f"\nPrevious attempt feedback: {feedback}\n" if feedback else ""
        return (
            "Complete the coding task below. Inspect the supplied workspace carefully and make "
            "the smallest complete set of file replacements needed. Do not invent files or APIs "
            "unless necessary. A replacement's content must be the entire resulting file. "
            "If key requirements are missing, set needs_user_input to true and do not edit files.\n\n"
            f"Goal:\n{goal}\n\n"
            f"Workspace:\n{context}\n"
            f"{retry_note}\n"
            "Return only valid JSON with exactly this shape:\n"
            "{\"summary\":\"short outcome\",\"plan\":[\"step\"],\"edits\":[{\"path\":\"relative/path.ext\",\"content\":\"complete file contents\",\"reason\":\"why\"}],\"needs_user_input\":false,\"question\":null}\n"
            "Use a relative path without '..'. Do not use Markdown fences."
        )

    @staticmethod
    def _workspace_context(goal: str, workspace: Dict[str, str]) -> str:
        """Select a bounded, deterministic subset of relevant workspace files."""
        goal_terms = set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{2,}", goal.lower()))

        def relevance(item: Tuple[str, str]) -> Tuple[int, str]:
            path, content = item
            haystack = f"{path}\n{content[:4000]}".lower()
            return (sum(term in haystack for term in goal_terms), path)

        chosen = sorted(workspace.items(), key=relevance, reverse=True)
        parts: List[str] = []
        used = 0
        for path, content in chosen:
            remaining = MAX_CONTEXT_CHARS - used
            if remaining <= 0:
                break
            excerpt = content[:remaining]
            parts.append(f"--- {path} ---\n{excerpt}")
            used += len(path) + len(excerpt) + 8
        return "\n\n".join(parts) or "(The workspace is empty.)"

    @staticmethod
    def _parse_decision(raw_response: str) -> Tuple[Dict[str, Any] | None, str | None]:
        text = raw_response.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
        decoder = json.JSONDecoder()
        for position, character in enumerate(text):
            if character != "{":
                continue
            try:
                value, _ = decoder.raw_decode(text[position:])
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                return value, None
        return None, "No JSON object found in model output."

    @staticmethod
    def _decision_from_code_snippet(
        raw_response: str, workspace: Dict[str, str], goal: str
    ) -> Dict[str, Any] | None:
        """
        Convert a conventional fenced code answer into one safe, reviewable edit.

        Smaller local models frequently answer coding prompts with a code block
        despite a structured-output instruction. This fallback is intentionally
        conservative: it only acts when one target file can be identified.
        """
        match = re.search(r"```(?P<language>[\w+-]*)\s*\n(?P<code>.*?)```", raw_response, re.DOTALL)
        if not match:
            return None

        code = match.group("code").strip()
        if not code:
            return None
        language = match.group("language").lower()
        path = CodingAgent._snippet_target_path(raw_response, language, workspace)
        if path is None:
            return None

        previous = workspace[path]
        content = code
        # A snippet is normally additive. Preserve an existing file unless the
        # response clearly includes it as a complete replacement.
        if previous.strip() and not code.lstrip().startswith(previous.strip()):
            content = f"{previous.rstrip()}\n\n{code}\n"
        elif not content.endswith("\n"):
            content += "\n"

        return {
            "summary": "Converted an unstructured model code snippet into a reviewable file edit.",
            "plan": [
                "Identify the unambiguous target file.",
                "Apply the returned code snippet as a minimal edit.",
                "Run a non-executing syntax check.",
            ],
            "edits": [{
                "path": path,
                "content": content,
                "reason": "The local model returned a code snippet instead of structured edit JSON.",
            }],
            "needs_user_input": False,
            "question": None,
        }

    @staticmethod
    def _snippet_target_path(
        raw_response: str, language: str, workspace: Dict[str, str]
    ) -> str | None:
        """Find an existing target for an unstructured code block without guessing."""
        explicit = re.search(
            r"(?:file|path)\s*[:=]\s*[`'\"]?([^`'\"\s:]+)",
            raw_response,
            re.IGNORECASE,
        )
        if explicit:
            candidate = explicit.group(1)
            if candidate in workspace and CodingAgent._safe_relative_path(candidate):
                return candidate

        extensions = {
            "python": {".py"},
            "py": {".py"},
            "javascript": {".js", ".mjs", ".cjs"},
            "js": {".js", ".mjs", ".cjs"},
            "typescript": {".ts", ".tsx"},
            "ts": {".ts", ".tsx"},
            "tsx": {".tsx"},
            "jsx": {".jsx"},
            "json": {".json"},
            "yaml": {".yaml", ".yml"},
            "yml": {".yaml", ".yml"},
            "html": {".html", ".htm"},
            "css": {".css"},
        }
        candidates = [
            path for path in workspace
            if PurePosixPath(path).suffix.lower() in extensions.get(language, set())
        ]
        if len(candidates) == 1:
            return candidates[0]
        if len(workspace) == 1:
            only_path = next(iter(workspace))
            return only_path if CodingAgent._safe_relative_path(only_path) else None
        return None

    def _validated_edits(
        self, raw_edits: Any, workspace: Dict[str, str]
    ) -> Tuple[List[AgentEdit], str | None]:
        if not isinstance(raw_edits, list):
            return [], "'edits' must be a JSON array."
        if len(raw_edits) > MAX_AGENT_EDITS:
            return [], f"At most {MAX_AGENT_EDITS} files may be edited in one iteration."

        edits: List[AgentEdit] = []
        seen_paths = set()
        for item in raw_edits:
            if not isinstance(item, dict):
                return [], "Each edit must be an object."
            path = item.get("path")
            content = item.get("content")
            if not isinstance(path, str) or not self._safe_relative_path(path):
                return [], f"Unsafe edit path: {path!r}."
            if path in seen_paths:
                return [], f"Duplicate edit path: {path}."
            if not isinstance(content, str):
                return [], f"Edit content for {path} must be text."
            if len(content.encode("utf-8")) > MAX_AGENT_FILE_SIZE:
                return [], f"Edit for {path} exceeds the file-size limit."
            seen_paths.add(path)
            edits.append(
                AgentEdit(
                    path=path,
                    content=content,
                    reason=self._as_string(item.get("reason")),
                    previous_content=workspace.get(path, ""),
                )
            )
        return edits, None

    @staticmethod
    def _safe_relative_path(path: str) -> bool:
        if not path or "\x00" in path or "\\" in path:
            return False
        candidate = PurePosixPath(path)
        return not candidate.is_absolute() and ".." not in candidate.parts and str(candidate) != "."

    @staticmethod
    def _as_string(value: Any, default: str = "") -> str:
        return value if isinstance(value, str) else default

    @staticmethod
    def _as_string_list(value: Any) -> List[str]:
        return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []

    @staticmethod
    def _verify_yaml(content: str) -> None:
        import yaml

        yaml.safe_load(content)

    def _verify_javascript(self, path: str, content: str) -> VerificationResult:
        node = shutil.which("node")
        if not node:
            self._verify_balanced_delimiters(content)
            return VerificationResult(path, "passed", "Delimiters balanced; Node.js is unavailable for parsing.")
        with tempfile.TemporaryDirectory(prefix="concode-js-check-") as directory:
            target = f"{directory}/check.js"
            with open(target, "w", encoding="utf-8") as handle:
                handle.write(content)
            result = subprocess.run(
                [node, "--check", target],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        if result.returncode:
            error = (result.stderr or result.stdout).strip().splitlines()
            raise ValueError(error[-1] if error else "JavaScript syntax check failed.")
        return VerificationResult(path, "passed", "JavaScript syntax parsed by Node.js.")

    @staticmethod
    def _verify_balanced_delimiters(content: str) -> None:
        """Conservative lexical delimiter check for languages without a safe parser."""
        pairs = {"(": ")", "[": "]", "{": "}"}
        closers = {value: key for key, value in pairs.items()}
        stack: List[str] = []
        quote: str | None = None
        escaped = False
        for character in content:
            if quote:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == quote:
                    quote = None
                continue
            if character in {"'", '"', "`"}:
                quote = character
            elif character in pairs:
                stack.append(character)
            elif character in closers:
                if not stack or stack.pop() != closers[character]:
                    raise ValueError("Unbalanced closing delimiter.")
        if quote:
            raise ValueError("Unterminated string literal.")
        if stack:
            raise ValueError("Unbalanced opening delimiter.")
