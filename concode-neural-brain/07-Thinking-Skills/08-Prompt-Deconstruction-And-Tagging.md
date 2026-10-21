---
title: Thinking Skill — Prompt Deconstruction & Tagging
type: thinking_skill
tags:
  - skill/prompt-deconstruction
  - nlp/tokenization
---

# Thinking Skill: Prompt Deconstruction & Tagging

> Deconstructs complex developer prompts into normalized entity tags, syntax targets, and technical domain identifiers prior to neural guild routing.

---

## Processing Pipeline

1. **Token Normalization**: Lowercases and strips non-syntactic noise characters.
2. **Entity Tag Extraction**: Matches technical identifiers (e.g. `jwt`, `three.js`, `postgres`, `null-pointer`, `solidity`).
3. **Intent Signal Scoring**: Weighs imperative verbs (`fix`, `create`, `optimize`, `test`, `deploy`) to compute domain probability distributions.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/01-Intent-Classifier|01-Intent-Classifier]]
- Master Dashboard: [[00-Dashboard/Dashboard|Dashboard]]
