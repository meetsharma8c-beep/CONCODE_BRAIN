---
title: Thinking Skill — KV-Cache Memory Allocation
type: thinking_skill
tags:
  - skill/kv-cache-memory
  - memory/tensor-allocation
---

# Thinking Skill: KV-Cache Memory Allocation

> Manages contiguous VRAM memory blocks for Key ($K$) and Value ($V$) tensors across 32 transformer layers.

---

## Memory Size Formula

$$\text{Memory}_{\text{KV}} = 2 \times b \times s \times l \times h \times d \times \text{bytes\_per\_element}$$

where $b=1$, $s=2048$, $l=32$, $h=32$, $d=128$, utilizing FP16 precision (~1.07 GB).

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/03-Core-LLM-Generator|03-Core-LLM-Generator]]
