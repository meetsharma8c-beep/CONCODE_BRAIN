---
title: Thinking Skill — Attention Masking & Padding
type: thinking_skill
tags:
  - skill/attention-masking
  - transformer/padding
---

# Thinking Skill: Attention Masking & Padding

> Applies causal attention masks to enforce directional generation and masks padding tokens during batched sequence processing.

---

## Causal Attention Mask Matrix

$$\mathbf{M}_{i,j} = \begin{cases} 0 & \text{if } i \ge j \\ -\infty & \text{if } i < j \end{cases}$$

- Softmax over $-\infty$ sets future token attention weights to exactly zero:
  $$\text{Softmax}\left(\frac{Q K^T}{\sqrt{d_k}} + \mathbf{M}\right)$$

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/03-Core-LLM-Generator|03-Core-LLM-Generator]]
