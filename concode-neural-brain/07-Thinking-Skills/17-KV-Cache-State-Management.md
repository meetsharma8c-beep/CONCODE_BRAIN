---
title: Thinking Skill — KV-Cache State Management
type: thinking_skill
tags:
  - skill/kv-cache
  - memory/decoding
---

# Thinking Skill: KV-Cache State Management

> Retains previous Key ($K$) and Value ($V$) layer projections across generation steps to achieve $O(1)$ per-token decoding time.

---

## State Update Equation

$$K_{1:t} = \left[ K_{1:t-1} \,;\, X_t W_K \right], \quad V_{1:t} = \left[ V_{1:t-1} \,;\, X_t W_V \right]$$

- Eliminates redundant matrix multiplications over previous tokens.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/03-Core-LLM-Generator|03-Core-LLM-Generator]]
