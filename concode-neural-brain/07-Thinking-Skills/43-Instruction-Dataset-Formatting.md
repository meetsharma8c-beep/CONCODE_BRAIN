---
title: Thinking Skill — Instruction Dataset Formatting
type: thinking_skill
tags:
  - skill/dataset-formatting
  - dataset/multi-guild
---

# Thinking Skill: Instruction Dataset Formatting

> Formats 5,500 multi-guild training examples into standardized prompt/response JSONL pairs.

---

## JSONL Schema Definition

```json
{
  "instruction": "Fix null pointer in login form",
  "input": "function login() { return user.name; }",
  "output": "function login() { return user && user.name ? user.name : null; }",
  "guild": "debugger"
}
```

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Dataset: [[03-Training-Data/Multi-Guild-Train|Multi-Guild-Train]]
