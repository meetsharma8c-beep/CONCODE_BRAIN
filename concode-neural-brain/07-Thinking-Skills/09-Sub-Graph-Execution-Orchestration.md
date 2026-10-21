---
title: Thinking Skill — Sub-Graph Execution Orchestration
type: thinking_skill
tags:
  - skill/orchestration
  - graph/pipeline
---

# Thinking Skill: Sub-Graph Execution Orchestration

> Orchestrates parallel execution sub-graphs across retrieval vector lookup, intent classification, LLM generation, and self-healing code repair.

---

## Execution Graph Topology

```
                  ┌─────────────────────────────────┐
                  │   Incoming Developer Prompt    │
                  └────────────────┬────────────────┘
                                   │
                  ┌────────────────┴────────────────┐
                  │                                 │
                  ▼                                 ▼
       ┌────────────────────┐            ┌────────────────────┐
       │ Intent Classifier  │            │ Workspace Retriever│
       │ (DistilBERT Logits)│            │ (FAISS Embeddings) │
       └──────────┬─────────┘            └──────────┬─────────┘
                  │                                 │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────┐
                  │    Core LLM Code Generator      │
                  │   (CodeLlama-7B Metal GPU)     │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────┐
                  │     Neural Code Repairer        │
                  │   (CodeT5 + Regex Balancer)     │
                  └─────────────────────────────────┘
```

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem Overview: [[01-Brain-Architecture/00-Brain-Overview|00-Brain-Overview]]
