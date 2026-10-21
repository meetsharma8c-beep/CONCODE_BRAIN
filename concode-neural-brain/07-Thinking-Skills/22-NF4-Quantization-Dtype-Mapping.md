---
title: Thinking Skill — NF4 Quantization Dtype Mapping
type: thinking_skill
tags:
  - skill/nf4-quantization
  - qlora/bitsandbytes
code_file: src/neural_network.py
---

# Thinking Skill: NF4 Quantization Dtype Mapping

> Maps 32-bit floating point model weights into 4-bit NormalFloat (NF4) representations for optimal memory footprint without precision loss.

---

## Quantization Binning Equation

$$q_i = \text{argmin}_k \left| w_i - c_k \right|$$

where $c_k$ are the 16 quantile points of a standard normal distribution $\mathcal{N}(0, 1)$.

- Reduces base 7B model VRAM footprint from 14 GB (FP16) down to ~3.8 GB (NF4).

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- QLoRA Experiment: [[04-Experiments/QLoRA-FineTuning|QLoRA-FineTuning]]
