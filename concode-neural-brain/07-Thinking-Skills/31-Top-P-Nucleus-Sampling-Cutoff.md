---
title: Thinking Skill — Top-P Nucleus Sampling Cutoff
type: thinking_skill
tags:
  - skill/top-p-sampling
  - math/nucleus-cutoff
---

# Thinking Skill: Top-P Nucleus Sampling Cutoff

> Filters token candidates to the smallest set whose cumulative probability mass exceeds threshold $p = 0.90$.

---

## Cumulative Probability Cutoff Equation

$$V^{(p)} = \text{argmin}_S \left( \sum_{x \in S} P(x \mid y_{<t}) \ge p \right)$$

- Re-normalizes probability mass over truncated subset $V^{(p)}$ before sampling token $y_t$.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/03-Core-LLM-Generator|03-Core-LLM-Generator]]
