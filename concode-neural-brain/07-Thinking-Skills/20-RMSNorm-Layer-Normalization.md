---
title: Thinking Skill — RMSNorm Layer Normalization
type: thinking_skill
tags:
  - skill/rmsnorm
  - math/normalization
---

# Thinking Skill: RMSNorm Layer Normalization

> Normalizes layer activations by root mean square, eliminating mean-centering calculations for 7B parameter speedup.

---

## Mathematical Formulation

$$\bar{a}_i = \frac{a_i}{\text{RMS}(\mathbf{a})} g_i, \quad \text{where } \text{RMS}(\mathbf{a}) = \sqrt{\frac{1}{d} \sum_{i=1}^{d} a_i^2 + \epsilon}$$

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Neural Process: [[01-Brain-Architecture/08-Neural-Thinking-Process|08-Neural-Thinking-Process]]
