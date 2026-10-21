---
title: Math Foundation -- RMSNorm Scaling
type: math_foundation
tags:
  - math/rmsnorm
  - math/normalization
---

# Math Foundation: RMSNorm Scaling

> Derivation of Root Mean Square Layer Normalization used in place of LayerNorm across all 32 CodeLlama transformer blocks.

---

## Derivation

Given input vector $\mathbf{x} \in \mathbb{R}^d$, standard LayerNorm computes:

$$\text{LayerNorm}(\mathbf{x}) = \frac{\mathbf{x} - \mu}{\sqrt{\sigma^2 + \epsilon}} \odot \gamma + \beta$$

RMSNorm simplifies by removing the mean-centering step. It normalizes by the root mean square statistic alone:

$$\text{RMS}(\mathbf{x}) = \sqrt{\frac{1}{d} \sum_{i=1}^d x_i^2}$$

$$\text{RMSNorm}(\mathbf{x}) = \frac{\mathbf{x}}{\text{RMS}(\mathbf{x}) + \epsilon} \odot \gamma$$

where $\gamma \in \mathbb{R}^d$ is a learned scale parameter and $\epsilon$ is a small constant for numerical stability (typically $10^{-6}$).

---

## Computational Advantage

RMSNorm eliminates the need to compute the mean $\mu$, reducing the normalization to a single reduction operation. For hidden dimension $d = 4096$, this saves one full pass over the vector per layer per token, yielding measurable latency reduction at inference time.

---

## Related Notes

- MOC: [[13-Mathematical-Foundations/Math-Foundations-MOC|Math-Foundations-MOC]]
- Thinking Skill: [[07-Thinking-Skills/20-RMSNorm-Layer-Normalization|20-RMSNorm-Layer-Normalization]]
