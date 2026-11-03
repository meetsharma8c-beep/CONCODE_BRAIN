---
title: Thinking Skill -- Executive DAG Goal Decomposition
type: thinking_skill
tags:
  - skill/dag-decomposition
  - subsystem/planner
---

# Thinking Skill: Executive DAG Goal Decomposition

> System-2 decomposition of complex goals into a topologically verified Directed Acyclic Graph (DAG) of dependency-ordered tasks with automatic backtracking.

---

## Topological Validation (Kahn's Algorithm)

Given a set of tasks $V$ and directed dependency edges $E = \{(u, v)\}$ meaning task $u$ must complete before task $v$:

1. Compute in-degree $\deg^-(v)$ for all $v \in V$.
2. Initialize queue $Q = \{v \in V \mid \deg^-(v) = 0\}$.
3. Pop $u \in Q$, increment visited counter, and decrement $\deg^-(w)$ for each dependent $w$.
4. If visited count equals $|V|$, the plan is acyclic and valid.

---

## State Machine Transitions

```
PENDING ---> EXECUTING ---> VERIFYING ---> COMPLETED
                 ^              |
                 |              v (attempt < max_attempts)
                 +--- BACKTRACKING
```

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/11-Executive-Meta-Planner|11-Executive-Meta-Planner]]
