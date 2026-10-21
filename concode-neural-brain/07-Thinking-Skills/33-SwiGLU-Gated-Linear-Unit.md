---
title: Thinking Skill — SwiGLU Gated Linear Unit
type: thinking_skill
tags:
  - skill/swiglu-activation
  - math/gated-unit
---

# Thinking Skill: SwiGLU Gated Linear Unit

> Computes Swish-gated element-wise product to expand feature representations 2.68x inside Feed-Forward Networks.

---

## SwiGLU Mathematical Definition

$$\text{SwiGLU}(x, W, V, W_2) = \left( \text{SiLU}(x W) \odot x V \right) W_2$$

where $\text{SiLU}(z) = z \cdot \sigma(z) = \frac{z}{1 + e^{-z}}$.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Neural Process: [[01-Brain-Architecture/08-Neural-Thinking-Process|08-Neural-Thinking-Process]]
