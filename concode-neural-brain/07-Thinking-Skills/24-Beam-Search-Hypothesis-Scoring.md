---
title: Thinking Skill — Beam Search Hypothesis Scoring
type: thinking_skill
tags:
  - skill/beam-search
  - repair/codet5
code_file: src/brain/repair.py
---

# Thinking Skill: Beam Search Hypothesis Scoring

> Maintains top-K candidate sequences during CodeT5 neural repair decoding using length-normalized log likelihood scores.

---

## Hypothesis Score Equation

$$\text{Score}(Y) = \frac{1}{|Y|^\alpha} \sum_{t=1}^{|Y|} \log P(y_t \mid y_{<t}, \mathbf{H})$$

where $\alpha = 0.6$ is the length penalty hyperparameter.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/04-Code-Repairer|04-Code-Repairer]]
