---
title: Thinking Skill — Dense Vector Similarity Search
type: thinking_skill
tags:
  - skill/vector-search
  - minilm/faiss
code_file: src/brain/retriever.py
---

# Thinking Skill: Dense Vector Similarity Search

> Encodes workspace code into 384-dimensional dense vectors and performs inner-product similarity search via FAISS.

---

## Mechanism & Math

- Splits file contents into 512-character chunks with 3-line overlaps.
- Embeds chunks using `all-MiniLM-L6-v2`.
- Normalizes vectors ($L_2$ norm) and builds a flat FAISS `IndexFlatIP` index:
  $$\text{Similarity}(q, d) = \frac{q \cdot d}{\|q\|_2 \|d\|_2}$$
- Injects Top-3 retrieved code snippets into the generator prompt context.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/02-Workspace-Retriever|02-Workspace-Retriever]]
