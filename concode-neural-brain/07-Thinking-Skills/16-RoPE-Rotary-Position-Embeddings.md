---
title: Thinking Skill — RoPE Rotary Position Embeddings
type: thinking_skill
tags:
  - skill/rope-embeddings
  - math/rotary-pos
---

# Thinking Skill: RoPE Rotary Position Embeddings

> Rotates 2D vector pairs by positional angles to preserve relative distance across long code tokens.

---

## Mathematical Formulation

$$\mathbf{R}_{\Theta, m}^d = \text{diag}\left( \mathbf{R}_{\theta_1, m}, \mathbf{R}_{\theta_2, m}, \dots, \mathbf{R}_{\theta_{d/2}, m} \right)$$

where $\mathbf{R}_{\theta_i, m}$ is the 2D rotation matrix:

$$\mathbf{R}_{\theta_i, m} = \begin{pmatrix} \cos(m \theta_i) & -\sin(m \theta_i) \\ \sin(m \theta_i) & \cos(m \theta_i) \end{pmatrix}$$

- Preserves relative token distance: $(R_m q)^T (R_n k) = q^T R_{n-m} k$.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Neural Process: [[01-Brain-Architecture/08-Neural-Thinking-Process|08-Neural-Thinking-Process]]
