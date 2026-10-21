---
title: Thinking Skill — Seq2Seq Neural Code Repair
type: thinking_skill
tags:
  - skill/neural-repair
  - codet5/seq2seq
code_file: src/brain/repair.py
---

# Thinking Skill: Seq2Seq Neural Code Repair

> Self-heals raw LLM code outputs using CodeT5 encoder-decoder sequence-to-sequence beam search (`beam_size=4`).

---

## Mechanism & Math

- Encodes broken code sequence: $\mathbf{H} = \text{Encoder}(\text{"fix: "} + \text{code})$.
- Decodes corrected sequence via beam search over target vocabulary:
  $$\hat{Y} = \arg\max_{Y} \sum_{t=1}^T \log P(y_t \mid y_{<t}, \mathbf{H})$$
- Returns repaired string and sets `repair_applied = True` flag if changed.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/04-Code-Repairer|04-Code-Repairer]]
