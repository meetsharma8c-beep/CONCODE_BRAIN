---
title: Thinking Skill — Gradient Checkpointing & Offloading
type: thinking_skill
tags:
  - skill/gradient-checkpointing
  - memory/offloading
---

# Thinking Skill: Gradient Checkpointing & Offloading

> Optimizes VRAM consumption during deep 32-layer transformer passes by recomputing intermediate activations on-demand.

---

## Mechanism

- Trades extra compute FLOPs for 60% VRAM reduction.
- Enables 7B parameter execution within 4 GB Metal GPU allocations.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Neural Process: [[01-Brain-Architecture/08-Neural-Thinking-Process|08-Neural-Thinking-Process]]
