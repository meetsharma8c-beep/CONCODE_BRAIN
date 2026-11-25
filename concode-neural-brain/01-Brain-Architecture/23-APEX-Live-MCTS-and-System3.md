---
title: APEX Live MCTS and System-3 Metacognitive Supervisor
type: architecture
tags:
  - system/brain
  - architecture/apex-v4
  - status/active
version: 4.0.0
---

# APEX Live MCTS and System-3 Metacognitive Supervisor

> Implementation: `src/brain/apex_reasoner.py`

Unified frontier reasoning orchestrator exposed via `POST /api/v1/apex`:
- **System-3 Metacognitive Supervisor**: Monitors semantic similarity ring buffer (`cosine_sim > 0.92`) and Lyapunov progress potential ($\Delta V_t$) to interrupt reasoning stalls and trigger forced `<backtrack>` pivots, while quantifying aleatoric vs. epistemic uncertainty.
- **Live Generative MCTS**: Runs UCT tree search over real LLM expansions scored deterministically by `FormalVerifier`, injecting compiler errors, CWE findings, and formal `unsat_core` witnesses into self-repair branches.
- **Continual Learning Flywheel**: Harvests verified trajectories, DPO preference pairs, and GraphRAG insights automatically.

## Linked Subsystems

- [[01-Brain-Architecture/18-APEX-Frontier-Architecture|18-APEX-Frontier-Architecture]]
- [[01-Brain-Architecture/21-Neural-Symbolic-Formal-Verifier|21-Neural-Symbolic-Formal-Verifier]]
- [[01-Brain-Architecture/22-Frontier-Sparse-MoE-Mesh|22-Frontier-Sparse-MoE-Mesh]]
- [[01-Brain-Architecture/17-Evolution-Harvester|17-Evolution-Harvester]]
