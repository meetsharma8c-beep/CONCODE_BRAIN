---
title: Thinking Skill — Token Probability Entropy Analysis
type: thinking_skill
tags:
  - skill/entropy-analysis
  - math/information-theory
---

# Thinking Skill: Token Probability Entropy Analysis

> Measures generation uncertainty by calculating Shannon entropy across top-k vocabulary logit distributions.

---

## Shannon Entropy Formula

$$H(X) = -\sum_{i=1}^{k} P(x_i) \log_2 P(x_i)$$

- High entropy ($H > 3.5$) signals generation ambiguity, triggering self-correction and code repair passes.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/04-Code-Repairer|04-Code-Repairer]]
