---
title: Thinking Skill — LoRA Rank And Alpha Scaling
type: thinking_skill
tags:
  - skill/lora-scaling
  - math/rank-decomposition
---

# Thinking Skill: LoRA Rank And Alpha Scaling

> Scales low-rank matrix update weights $B \cdot A$ by constant factor $\frac{\alpha}{r}$ ($r=64, \alpha=128$).

---

## Scaling Equation

$$\Delta W = \frac{\alpha}{r} \cdot (B \cdot A) = 2.0 \cdot (B \cdot A)$$

where $A \in \mathbb{R}^{r \times k}$ and $B \in \mathbb{R}^{d \times r}$.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- QLoRA Experiment: [[04-Experiments/QLoRA-FineTuning|QLoRA-FineTuning]]
