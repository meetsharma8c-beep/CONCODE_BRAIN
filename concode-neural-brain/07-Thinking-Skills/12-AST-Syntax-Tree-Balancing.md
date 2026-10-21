---
title: Thinking Skill — AST Syntax Tree Balancing
type: thinking_skill
tags:
  - skill/ast-balancing
  - syntax/healing
---

# Thinking Skill: AST Syntax Tree Balancing

> Inspects abstract syntax trees to balance unclosed scopes, missing braces, and function signature terminations.

---

## Mechanism

1. **Token Stack Analysis**: Pushes open delimiters (`{`, `[`, `(`) and matches closing tokens.
2. **Scope Auto-Closure**: Appends missing delimiters in inverse LIFO order.
3. **AST Validation**: Validates generated code block against Python / JS language grammar specs.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/04-Code-Repairer|04-Code-Repairer]]
