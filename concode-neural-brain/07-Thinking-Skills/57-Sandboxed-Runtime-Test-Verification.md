---
title: Thinking Skill -- Sandboxed Runtime Test Verification
type: thinking_skill
tags:
  - skill/sandbox-verification
  - subsystem/sandbox
---

# Thinking Skill: Sandboxed Runtime Test Verification

> Materializes candidate workspace edits inside an isolated temporary filesystem and executes unit test suites with sanitized environments and strict timeout quotas.

---

## Isolation Controls

| Control | Implementation |
|---------|----------------|
| **Filesystem Isolation** | Ephemeral `tempfile.TemporaryDirectory` (`concode-sandbox-*`) |
| **Environment Stripping** | Only `PATH`, `HOME`, `TMPDIR`, `PYTHONPATH`, `PYTHONNOUSERSITE=1` |
| **Interpreter Flags** | `python -B -s -m unittest` (no bytecode, no user site-packages) |
| **Timeout Quota** | Hard subprocess timeout (`SANDBOX_TIMEOUT_SECONDS = 5.0`) |
| **Output Cap** | Truncated at `32,768` bytes per stream (`stdout` / `stderr`) |

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/12-Sandboxed-Runtime-Executor|12-Sandboxed-Runtime-Executor]]
