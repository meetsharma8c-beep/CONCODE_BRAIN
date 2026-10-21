---
title: Thinking Skill — QLoRA Adapter Pathway Modulation
type: thinking_skill
tags:
  - skill/qlora-modulation
  - moe/adapter-routing
code_file: src/neural_network.py
---

# Thinking Skill: QLoRA Adapter Pathway Modulation

> Modulates attention and FFN layer projections via specialized LoRA adapter matrices ($r=64, \alpha=128$).

---

## Mechanism & Math

- Applies low-rank adapter projections across 224 weight matrices:
  $$W_{\text{effective}} = W_{\text{base}} + \left(B \cdot A\right) \times \frac{\alpha}{r}$$
- Channels representations through domain-specific expert sub-network pathways for 13 technical guilds.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Fine-Tuning: [[04-Experiments/QLoRA-FineTuning|QLoRA-FineTuning]]
- Guilds Overview: [[02-Guilds/Guild-Overview|Guild-Overview]]
