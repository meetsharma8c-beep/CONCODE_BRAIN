---
title: Math Foundation -- Cross-Entropy Sequence Loss
type: math_foundation
tags:
  - math/cross-entropy
  - math/loss-function
---

# Math Foundation: Cross-Entropy Sequence Loss

> Derivation of the token-level cross-entropy loss function used during QLoRA fine-tuning of CodeLlama.

---

## Derivation

For an autoregressive language model generating sequence $\mathbf{y} = (y_1, y_2, \ldots, y_T)$, the per-token cross-entropy loss at position $t$ is:

$$\mathcal{L}_t = -\log p_\theta(y_t \mid y_{<t})$$

where $p_\theta(y_t \mid y_{<t})$ is the softmax probability assigned to the ground-truth token $y_t$ given all preceding tokens.

The sequence-level loss averages over all $T$ tokens:

$$\mathcal{L}(\theta) = -\frac{1}{T} \sum_{t=1}^T \log p_\theta(y_t \mid y_{<t}) = -\frac{1}{T} \sum_{t=1}^T \log \frac{\exp(z_{y_t})}{\sum_{j=1}^V \exp(z_j)}$$

where $z_j$ is the logit for vocabulary token $j$ and $V$ is the vocabulary size (32,000 for CodeLlama).

---

## Gradient Signal

The gradient of cross-entropy with respect to logit $z_k$ at position $t$:

$$\frac{\partial \mathcal{L}_t}{\partial z_k} = p_\theta(k \mid y_{<t}) - \mathbb{1}[k = y_t]$$

This gradient equals the predicted probability minus the one-hot target, providing a clean signal that shrinks as the model converges.

---

## Related Notes

- MOC: [[13-Mathematical-Foundations/Math-Foundations-MOC|Math-Foundations-MOC]]
- Thinking Skill: [[07-Thinking-Skills/28-Loss-Function-Cross-Entropy-Computation|28-Loss-Function-Cross-Entropy-Computation]]
