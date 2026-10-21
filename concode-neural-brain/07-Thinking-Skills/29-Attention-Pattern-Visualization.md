---
title: Thinking Skill — Attention Pattern Visualization
type: thinking_skill
tags:
  - skill/attention-visualization
  - interpretability/attention
---

# Thinking Skill: Attention Pattern Visualization

> Extracts 2D attention matrices across 32 layers for interpretability and reasoning graph verification.

---

## Matrix Representation

$$\mathbf{A}^{(l, h)} \in \mathbb{R}^{T \times T}, \quad A_{i,j}^{(l,h)} = \frac{\exp(q_i^T k_j / \sqrt{d_k})}{\sum_k \exp(q_i^T k_k / \sqrt{d_k})}$$

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Neural Process: [[01-Brain-Architecture/08-Neural-Thinking-Process|08-Neural-Thinking-Process]]
