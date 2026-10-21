---
title: Math Foundation -- Cosine Vector Similarity
type: math_foundation
tags:
  - math/cosine-similarity
  - math/retrieval
---

# Math Foundation: Cosine Vector Similarity

> Derivation of cosine similarity metric used in MiniLM dense vector retrieval for workspace code context injection.

---

## Derivation

Given query embedding $\mathbf{q} \in \mathbb{R}^d$ and document embedding $\mathbf{d} \in \mathbb{R}^d$, cosine similarity measures angular proximity:

$$\text{cos}(\mathbf{q}, \mathbf{d}) = \frac{\mathbf{q} \cdot \mathbf{d}}{||\mathbf{q}|| \cdot ||\mathbf{d}||} = \frac{\sum_{i=1}^d q_i d_i}{\sqrt{\sum_{i=1}^d q_i^2} \cdot \sqrt{\sum_{i=1}^d d_i^2}}$$

When vectors are L2-normalized ($||\mathbf{q}|| = ||\mathbf{d}|| = 1$), cosine similarity reduces to inner product:

$$\text{cos}(\mathbf{q}, \mathbf{d}) = \mathbf{q} \cdot \mathbf{d} = \mathbf{q}^T \mathbf{d}$$

This normalization identity is the reason the retriever uses `faiss.IndexFlatIP` (Inner Product) after applying L2 normalization, rather than `IndexFlatL2`.

---

## Relationship to L2 Distance

For L2-normalized vectors, cosine similarity and Euclidean distance are monotonically related:

$$||\mathbf{q} - \mathbf{d}||^2 = 2 - 2 \cdot \text{cos}(\mathbf{q}, \mathbf{d})$$

Maximizing cosine similarity is equivalent to minimizing L2 distance when vectors are unit-length.

---

## Related Notes

- MOC: [[13-Mathematical-Foundations/Math-Foundations-MOC|Math-Foundations-MOC]]
- Thinking Skill: [[07-Thinking-Skills/21-FAISS-L2-Vector-Normalization|21-FAISS-L2-Vector-Normalization]]
- Thinking Skill: [[07-Thinking-Skills/39-FAISS-IndexFlatIP-Inner-Product|39-FAISS-IndexFlatIP-Inner-Product]]
