---
title: Thinking Skill — FAISS Index Save And Reload
type: thinking_skill
tags:
  - skill/faiss-persistence
  - vector-search/faiss
---

# Thinking Skill: FAISS Index Save And Reload

> Serializes built FAISS vector search indices to disk (`data/faiss.index`) for zero-latency server cold boots.

---

## I/O Operations

```python
# Save Index
faiss.write_index(index, "data/faiss.index")

# Reload Index
index = faiss.read_index("data/faiss.index")
```

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/02-Workspace-Retriever|02-Workspace-Retriever]]
