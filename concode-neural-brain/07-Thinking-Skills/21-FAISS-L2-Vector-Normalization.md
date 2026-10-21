---
title: Thinking Skill — FAISS L2 Vector Normalization
type: thinking_skill
tags:
  - skill/l2-normalization
  - vector-search/faiss
code_file: src/brain/retriever.py
---

# Thinking Skill: FAISS L2 Vector Normalization

> Normalizes 384-dimensional MiniLM embeddings to unit length ($L_2$ norm = 1.0) so inner-product FAISS queries equal cosine similarity.

---

## Normalization Formula

$$\hat{\mathbf{v}} = \frac{\mathbf{v}}{\|\mathbf{v}\|_2} = \frac{\mathbf{v}}{\sqrt{\sum_{i=1}^{384} v_i^2}}$$

- Inner product of normalized vectors: $\hat{\mathbf{q}} \cdot \hat{\mathbf{d}} = \cos(\theta)$.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/02-Workspace-Retriever|02-Workspace-Retriever]]
