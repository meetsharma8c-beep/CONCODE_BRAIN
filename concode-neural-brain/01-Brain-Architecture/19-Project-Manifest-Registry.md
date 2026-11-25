---
title: Cross-Project Manifest Registry
type: architecture
tags:
  - system/brain
  - architecture/apex-v4
  - status/active
version: 4.0.0
---

# Cross-Project Manifest Registry

> Implementation: `src/brain/project_manifest.py`

Decouples the CONCODE Neural Brain from single-project assumptions by maintaining a persistent `ProjectManifestRegistry` (`data/project_manifests.json`). Any future startup, microservice, or consumer application can register its `<project_manifest>` dynamically via `POST /api/v1/projects/register` and bind its tech stack, pinned invariants, and UI action contract zero-shot at inference time.

## Linked Subsystems

- [[01-Brain-Architecture/18-APEX-Frontier-Architecture|18-APEX-Frontier-Architecture]]
- [[01-Brain-Architecture/20-Lifelong-Temporal-GraphRAG|20-Lifelong-Temporal-GraphRAG]]
- [[01-Brain-Architecture/23-APEX-Live-MCTS-and-System3|23-APEX-Live-MCTS-and-System3]]
