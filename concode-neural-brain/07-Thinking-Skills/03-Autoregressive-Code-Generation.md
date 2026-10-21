---
title: Thinking Skill — Autoregressive Code Generation
type: thinking_skill
tags:
  - skill/generation
  - codellama/transformer
code_file: src/brain/generator.py
---

# Thinking Skill: Autoregressive Code Generation

> Executes 32-layer transformer forward passes to generate code token-by-token using CodeLlama-7B GGUF on Metal GPU.

---

## Mechanism & Math

- Processes instruct-formatted prompt ($[INST] \ll SYS \gg ... [/INST]$).
- Computes multi-head attention across 1,024 attention heads.
- Applies nucleus sampling ($\text{temperature} = 0.3, \text{top\_p} = 0.9$) over vocabulary logits ($32,016$ dims).

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/03-Core-LLM-Generator|03-Core-LLM-Generator]]
- Neural Process: [[01-Brain-Architecture/08-Neural-Thinking-Process|08-Neural-Thinking-Process]]
