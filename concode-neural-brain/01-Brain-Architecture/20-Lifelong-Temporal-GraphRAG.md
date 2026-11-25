---
title: Lifelong Temporal GraphRAG Engine
type: architecture
tags:
  - system/brain
  - architecture/apex-v4
  - status/active
version: 4.0.0
---

# Lifelong Temporal GraphRAG Engine

> Implementation: `src/brain/graph_rag.py`

Persistent directed multigraph (`data/knowledge_graph.json`) combining project-scoped entities, exponential temporal decay ($w(t) = w_0 e^{-\lambda(t - t_0)}$) for episodic knowledge, and sticky pinning (`pinned=True`, $\lambda=0$) for immutable security, financial, architectural, and life-safety invariants. Injects k-hop BFS subgraphs as `<graph_rag_context>` directly into every APEX solve.

## Linked Subsystems

- [[01-Brain-Architecture/18-APEX-Frontier-Architecture|18-APEX-Frontier-Architecture]]
- [[01-Brain-Architecture/19-Project-Manifest-Registry|19-Project-Manifest-Registry]]
- [[01-Brain-Architecture/15-Cognitive-Memory-Manager|15-Cognitive-Memory-Manager]]
