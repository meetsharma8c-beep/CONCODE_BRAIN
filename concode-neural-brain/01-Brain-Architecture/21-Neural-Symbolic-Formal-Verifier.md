---
title: Neural-Symbolic Formal Verifier and GRPO Judge
type: architecture
tags:
  - system/brain
  - architecture/apex-v4
  - status/active
version: 4.0.0
---

# Neural-Symbolic Formal Verifier and GRPO Judge

> Implementation: `src/brain/formal_verifier.py`

Deterministic proof and verification layer exposed via `POST /api/v1/verify` and embedded inside every APEX MCTS/MoA loop:
- Native Z3 SMT linear constraint prover (with exact integer fallback) returning `PROVEN_SAT` witnesses or minimal `unsat_core` conflict sets.
- Directed wait-for graph deadlock cycle prover.
- Multi-language syntax and compilation verifier (Python, TypeScript, Go, Rust).
- AST and static security taint auditor (CWE-78, CWE-89, CWE-94, CWE-208, CWE-400, CWE-798).
- Composite GRPO reward judge and group advantage normalizer.

## Linked Subsystems

- [[01-Brain-Architecture/18-APEX-Frontier-Architecture|18-APEX-Frontier-Architecture]]
- [[01-Brain-Architecture/22-Frontier-Sparse-MoE-Mesh|22-Frontier-Sparse-MoE-Mesh]]
- [[01-Brain-Architecture/23-APEX-Live-MCTS-and-System3|23-APEX-Live-MCTS-and-System3]]
