---
title: Thinking Skill — Loss Function Cross Entropy Computation
type: thinking_skill
tags:
  - skill/cross-entropy
  - math/loss-function
---

# Thinking Skill: Loss Function Cross Entropy Computation

> Measures autoregressive target token prediction error during QLoRA adapter fine-tuning.

---

## Cross-Entropy Loss Equation

$$\mathcal{L}_{\text{CE}} = -\frac{1}{N} \sum_{i=1}^{N} \log P(y_i \mid y_{<i}, X)$$

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- QLoRA Experiment: [[04-Experiments/QLoRA-FineTuning|QLoRA-FineTuning]]
