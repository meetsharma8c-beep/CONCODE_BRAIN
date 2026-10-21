---
title: Math Foundation — Softmax Temperature
type: math_foundation
tags:
  - math/softmax
  - math/temperature
---

# Math Foundation: Softmax Temperature

> Derivation of temperature scaling over vocabulary logit vectors $\mathbf{z} \in \mathbb{R}^V$.

---

## Derivation

Let $z_i$ denote unnormalized logit for token $i$. Temperature scaling modifies logits prior to exponentiation:

$$p_i(T) = \frac{\exp(z_i / T)}{\sum_{j=1}^V \exp(z_j / T)}$$

As $T \to 0$:

$$\lim_{T \to 0^+} p_i(T) = \begin{cases} 1 & \text{if } i = \arg\max_k z_k \\ 0 & \text{otherwise} \end{cases}$$

---

## Related Notes

- MOC: [[13-Mathematical-Foundations/Math-Foundations-MOC|Math-Foundations-MOC]]
- Thinking Skill: [[07-Thinking-Skills/18-Softmax-Temperature-Scaling|18-Softmax-Temperature-Scaling]]
