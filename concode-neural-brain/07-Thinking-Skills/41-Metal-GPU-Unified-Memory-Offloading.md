---
title: Thinking Skill — Metal GPU Unified Memory Offloading
type: thinking_skill
tags:
  - skill/metal-gpu
  - hardware/apple-silicon
---

# Thinking Skill: Metal GPU Unified Memory Offloading

> Offloads 32 transformer layer weight tensors directly to Apple Silicon Metal GPU unified memory (`n_gpu_layers=99`).

---

## Hardware Execution Vector

```
CPU (M1/M2/M3 Max) <---> Unified LPDDR5 RAM (16/32/64 GB) <---> Metal Performance Shaders
```

- Zero-copy tensor sharing between CPU and GPU compute kernels.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/03-Core-LLM-Generator|03-Core-LLM-Generator]]
