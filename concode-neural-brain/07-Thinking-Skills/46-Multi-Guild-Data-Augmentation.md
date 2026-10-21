---
title: Thinking Skill — Multi-Guild Data Augmentation
type: thinking_skill
tags:
  - skill/data-augmentation
  - dataset/repair
---

# Thinking Skill: Multi-Guild Data Augmentation

> Synthesizes realistic syntax bugs, missing imports, and type errors to generate 10,000 code repair pairs for CodeT5 fine-tuning.

---

## Mutation Operators

1. **Delimiter Injection**: Strips closing braces (`}`, `]`, `)`).
2. **Keyword Perturbation**: Mutates language keywords (`function` → `functoin`).
3. **Null Access Injection**: Replaces safe property access (`obj?.prop`) with direct dereference (`obj.prop`).

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Dataset: [[03-Training-Data/Repair-Dataset|Repair-Dataset]]
