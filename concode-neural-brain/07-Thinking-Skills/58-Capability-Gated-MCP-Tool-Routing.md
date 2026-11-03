---
title: Thinking Skill -- Capability-Gated MCP Tool Routing
type: thinking_skill
tags:
  - skill/tool-routing
  - subsystem/tools
---

# Thinking Skill: Capability-Gated MCP Tool Routing

> Routes internal and external Model Context Protocol (MCP) tool invocations through a strict capability permission gate (`READ_ONLY`, `SANDBOX_EXEC`, `WORKSPACE_WRITE`, `EXTERNAL_NETWORK`).

---

## Built-in Tool Matrix

| Tool Name | Required Permission | Purpose |
|-----------|---------------------|---------|
| `workspace_search` | `READ_ONLY` | Regex search across workspace snapshot |
| `ast_inspect` | `READ_ONLY` | Extract classes, functions, imports, and line metrics |
| `math_evaluate` | `READ_ONLY` | Safe AST-based mathematical expression evaluation |
| `vault_query` | `READ_ONLY` | Retrieve relevant notes from the Obsidian vault |
| `git_status_diff` | `READ_ONLY` | Inspect repository branch, status, and diff stats |
| `sandbox_run` | `SANDBOX_EXEC` | Execute code inside the isolated sandbox |
| `filesystem_transaction` | `WORKSPACE_WRITE` | Atomic multi-file write with rollback on error |
| `web_fetch` | `EXTERNAL_NETWORK` | SSRF-protected HTTPS documentation fetcher |

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/13-Universal-Tool-Bus|13-Universal-Tool-Bus]]
