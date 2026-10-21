---
title: Thinking Skill — Regex Keyword Typo Correction Dictionary
type: thinking_skill
tags:
  - skill/typo-correction
  - repair/heuristics
---

# Thinking Skill: Regex Keyword Typo Correction Dictionary

> Maps common language keyword hallucinations to valid syntactical tokens via regex replacements.

---

## Replacement Mapping Table

| Hallucinated Pattern | Target Keyword | Target Language |
|----------------------|----------------|-----------------|
| `functoin` | `function` | JavaScript / TypeScript |
| `cosnt` | `const` | JavaScript / TypeScript |
| `retun` | `return` | General |
| `defination` | `def` | Python |

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/04-Code-Repairer|04-Code-Repairer]]
