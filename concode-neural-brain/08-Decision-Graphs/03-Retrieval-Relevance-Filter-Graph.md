---
title: Decision Graph — Retrieval Relevance Filter
type: decision_graph
tags:
  - graph/retrieval
  - decision/vector-filter
---

# Decision Graph: Retrieval Relevance Filter

> Decision pipeline evaluating workspace code context relevance before injecting into generator prompt.

---

## Flowchart Graph

```mermaid
graph TD
    Start[User Query] --> EmbedQuery[MiniLM Embedding Generation]
    EmbedQuery --> FAISSQuery[FAISS Index Inner Product Search]
    FAISSQuery --> TopK[Fetch Top-K Chunks]
    
    TopK --> FilterThreshold{Cosine Similarity >= 0.45?}
    FilterThreshold -->|Yes| RetainChunk[Keep Chunk in Context]
    FilterThreshold -->|No| DiscardChunk[Discard Irrelevant Chunk]
    
    RetainChunk --> TruncateWindow{Total Tokens <= 1024?}
    TruncateWindow -->|Yes| FormatContext[Inject Code Blocks into Prompt]
    TruncateWindow -->|No| PruneLowest[Prune Lowest Scoring Chunks]
    PruneLowest --> FormatContext
```

---

## Related Notes

- MOC: [[08-Decision-Graphs/Decision-Graphs-MOC|Decision-Graphs-MOC]]
- Subsystem: [[01-Brain-Architecture/02-Workspace-Retriever|02-Workspace-Retriever]]
