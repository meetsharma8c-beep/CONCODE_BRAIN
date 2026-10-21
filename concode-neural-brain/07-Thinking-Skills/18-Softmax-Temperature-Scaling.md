---
title: Thinking Skill — Softmax Temperature Scaling
type: thinking_skill
tags:
  - skill/temperature-scaling
  - math/probability
---

# Thinking Skill: Softmax Temperature Scaling

> Calibrates vocabulary probability distributions using temperature scaling parameter $T$.

---

## Logit Transformation Equation

$$P(x_i) = \frac{\exp(z_i / T)}{\sum_{j} \exp(z_j / T)}$$

- Low temperature ($T = 0.2$–$0.3$) sharpens distributions for precise, deterministic code syntax.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/03-Core-LLM-Generator|03-Core-LLM-Generator]]
