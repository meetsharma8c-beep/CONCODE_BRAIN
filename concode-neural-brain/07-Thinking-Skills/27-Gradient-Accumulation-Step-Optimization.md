---
title: Thinking Skill — Gradient Accumulation Step Optimization
type: thinking_skill
tags:
  - skill/gradient-accumulation
  - qlora/training
---

# Thinking Skill: Gradient Accumulation Step Optimization

> Accumulates gradients over $K=4$ micro-batches before performing weight updates to simulate larger effective batch sizes on limited GPU VRAM.

---

## Weight Update Formula

$$g_{\text{accum}} = \frac{1}{K} \sum_{k=1}^{K} \nabla_\theta \mathcal{L}_k, \quad \theta \leftarrow \theta - \eta \cdot \text{AdamW}(g_{\text{accum}})$$

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- QLoRA Experiment: [[04-Experiments/QLoRA-FineTuning|QLoRA-FineTuning]]
