---
title: Thinking Skill — AdamW Weight Decay Optimization
type: thinking_skill
tags:
  - skill/adamw-optimization
  - math/optimizer
---

# Thinking Skill: AdamW Weight Decay Optimization

> Decouples weight decay regularization from gradient updates during QLoRA adapter fine-tuning.

---

## Update Equations

$$\theta_t = \theta_{t-1} - \eta_t \lambda \theta_{t-1} - \frac{\eta_t}{\sqrt{\hat{v}_t} + \epsilon} \hat{m}_t$$

- Prevents weight magnitude explosion across 160M LoRA adapter parameters.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- QLoRA Experiment: [[04-Experiments/QLoRA-FineTuning|QLoRA-FineTuning]]
