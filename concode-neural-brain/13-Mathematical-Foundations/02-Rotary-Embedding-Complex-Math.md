---
title: Math Foundation — Rotary Embedding Complex Math
type: math_foundation
tags:
  - math/rope
  - math/complex-rotation
---

# Math Foundation: Rotary Embedding Complex Math

> Representing 2D vector rotations in complex plane $\mathbb{C}^{d/2}$ for relative positional embeddings.

---

## Complex Formulation

Let vector pair $(x_{2i-1}, x_{2i})$ be represented as complex number $z_i = x_{2i-1} + i x_{2i} \in \mathbb{C}$.

Rotary embedding multiplies by complex phase factor $\exp(i m \theta_i)$:

$$R_{\Theta, m}(z_i) = z_i \cdot e^{i m \theta_i} = (x_{2i-1} + i x_{2i}) (\cos(m\theta_i) + i \sin(m\theta_i))$$

---

## Related Notes

- MOC: [[13-Mathematical-Foundations/Math-Foundations-MOC|Math-Foundations-MOC]]
- Thinking Skill: [[07-Thinking-Skills/16-RoPE-Rotary-Position-Embeddings|16-RoPE-Rotary-Position-Embeddings]]
