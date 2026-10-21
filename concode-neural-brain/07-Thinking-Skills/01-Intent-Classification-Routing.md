---
title: Thinking Skill — Intent Classification Routing
type: thinking_skill
tags:
  - skill/intent
  - distilbert/routing
code_file: src/brain/intent.py
---

# Thinking Skill: Intent Classification Routing

> Classifies user prompts into 1 of 13 specialized technical domains using DistilBERT softmax logits.

---

## Mechanism & Math

- Computes sequence classification logits over 13 domain classes:
  $$P(\text{guild}_k \mid \text{text}) = \frac{e^{z_k}}{\sum_{j=1}^{13} e^{z_j}}$$
- Returns predicted guild and confidence score ($0.0 – 1.0$).
- Falls back to keyword density scoring if neural classifier weights are uninitialized.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/01-Intent-Classifier|01-Intent-Classifier]]
- Guild Index: [[02-Guilds/Guild-Overview|Guild-Overview]]
