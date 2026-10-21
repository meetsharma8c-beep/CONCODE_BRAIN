---
title: Thinking Skill — Regex Bracket & Typo Fixing
type: thinking_skill
tags:
  - skill/regex-repair
  - heuristics/fallback
code_file: src/brain/repair.py
---

# Thinking Skill: Regex Bracket & Typo Fixing

> Rule-based fallback engine repairing keyword typos and unclosed brackets (`(`, `[`, `{`).

---

## Mechanism & Math

- Replaces common keyword hallucinations (`functoin` → `function`, `cosnt` → `const`, `retun` → `return`).
- Scans string pushing/popping bracket symbols to an explicit LIFO stack.
- Appends missing closing brackets at end of file.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/04-Code-Repairer|04-Code-Repairer]]
