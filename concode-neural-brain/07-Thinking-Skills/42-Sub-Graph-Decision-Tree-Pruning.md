---
title: Thinking Skill — Sub-Graph Decision Tree Pruning
type: thinking_skill
tags:
  - skill/decision-tree-pruning
  - optimization/latency
---

# Thinking Skill: Sub-Graph Decision Tree Pruning

> Prunes unnecessary retrieval or repair sub-graphs when queries contain complete code snippets or explicit guild directives.

---

## Early Exit Condition

$$\text{Skip\_Retriever} = \text{Is\_Self\_Contained\_Code}(Q) \quad \lor \quad \text{Is\_Simple\_Greeting}(Q)$$

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/01-Intent-Classifier|01-Intent-Classifier]]
