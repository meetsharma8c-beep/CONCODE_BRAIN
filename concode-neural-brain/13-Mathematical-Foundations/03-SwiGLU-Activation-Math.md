---
title: Math Foundation -- SwiGLU Activation
type: math_foundation
tags:
  - math/swiglu
  - math/activation
---

# Math Foundation: SwiGLU Activation

> Derivation of the Gated Linear Unit variant used in CodeLlama's feed-forward network sublayers.

---

## Derivation

Standard GLU splits input $\mathbf{x}$ into two halves and applies a gating sigmoid:

$$\text{GLU}(\mathbf{x}, \mathbf{W}, \mathbf{V}) = (\mathbf{x} \mathbf{W}) \otimes \sigma(\mathbf{x} \mathbf{V})$$

SwiGLU replaces the sigmoid gate $\sigma$ with the Swish activation $\text{Swish}_\beta(x) = x \cdot \sigma(\beta x)$:

$$\text{SwiGLU}(\mathbf{x}, \mathbf{W}, \mathbf{V}, \mathbf{W}_2) = (\text{Swish}_1(\mathbf{x} \mathbf{W}) \otimes (\mathbf{x} \mathbf{V})) \mathbf{W}_2$$

where $\otimes$ denotes element-wise (Hadamard) product and $\sigma$ is the logistic sigmoid.

Setting $\beta = 1$ yields:

$$\text{Swish}_1(z) = z \cdot \sigma(z) = \frac{z}{1 + e^{-z}}$$

The derivative for backpropagation:

$$\frac{d}{dz} \text{Swish}_1(z) = \sigma(z) + z \cdot \sigma(z)(1 - \sigma(z)) = \sigma(z)(1 + z(1 - \sigma(z)))$$

---

## Implementation Context

CodeLlama uses SwiGLU in all 32 transformer blocks within the MLP sublayer. The hidden dimension expands from 4096 to $\frac{2}{3} \cdot 4 \cdot 4096 = 11008$ to compensate for the parameter increase from the additional gate projection.

---

## Related Notes

- MOC: [[13-Mathematical-Foundations/Math-Foundations-MOC|Math-Foundations-MOC]]
- Thinking Skill: [[07-Thinking-Skills/33-SwiGLU-Gated-Linear-Unit|33-SwiGLU-Gated-Linear-Unit]]
