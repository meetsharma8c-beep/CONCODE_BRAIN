---
title: Thinking Skill — Context Window Pruning Strategy
type: thinking_skill
tags:
  - skill/context-pruning
  - memory/optimization
---

# Thinking Skill: Context Window Pruning Strategy

> Dynamically prunes long file contents and conversation history to enforce token context boundaries under 4,096 tokens.

---

## Pruning Heuristics

1. **Relevance Thresholding**: Drops retrieved code chunks with FAISS cosine similarity below 0.45.
2. **Sliding Conversation Window**: Retains only the most recent 3 turns (6 messages).
3. **AST Skeleton Truncation**: Replaces function bodies in non-target files with `...` placeholders to conserve tokens.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/02-Workspace-Retriever|02-Workspace-Retriever]]
