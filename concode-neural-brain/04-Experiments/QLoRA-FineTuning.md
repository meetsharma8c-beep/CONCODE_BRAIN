---
title: QLoRA Fine-Tuning & Adapter Architecture
type: experiment
tags:
  - experiment/qlora
  - model/codellama
  - hardware/colab-t4
  - peft/unsloth
base_model: unsloth/codellama-7b-instruct-bnb-4bit
trainable_parameters: 160,000,000
lora_rank: 64
lora_alpha: 128
code_file: src/neural_network.py
---

# QLoRA Fine-Tuning & Adapter Architecture

> **Parameter-Efficient Fine-Tuning (PEFT)** of CodeLlama-7B across **224 LoRA adapter matrices** via Unsloth on Google Colab T4 GPU.

---

## Architecture & Mathematics

Rather than updating all 6.74 billion parameters, QLoRA freezes the base 4-bit quantized model and injects trainable rank decomposition matrices into every projection layer:

$$W' = W_{\text{base}} + (B \cdot A) \times \frac{\alpha}{r}$$

Where:
- **Rank ($r$)**: `64`
- **Alpha ($\alpha$)**: `128`
- **Scaling factor ($\alpha / r$)**: `2.0`
- **Trainable parameters**: ~160M across 224 matrices ($7 \text{ modules} \times 32 \text{ layers} \times 2$)

---

## Target Projection Modules

Adapters are attached to all 7 core projection components of the transformer blocks:

1. `q_proj` (Attention Query projection)
2. `k_proj` (Attention Key projection)
3. `v_proj` (Attention Value projection)
4. `o_proj` (Attention Output projection)
5. `gate_proj` (SwiGLU FFN Gate)
6. `up_proj` (SwiGLU FFN Up projection)
7. `down_proj` (SwiGLU FFN Down projection)

---

## Training Config & Execution

```python
# src/neural_network.py
MODEL_NAME = "unsloth/codellama-7b-instruct-bnb-4bit"
LORA_R = 64
LORA_ALPHA = 128
BATCH_SIZE = 2
GRAD_ACCUM = 4
LEARNING_RATE = 2e-4
MAX_STEPS = 300
OPTIMIZER = "adamw_8bit"
```

---

## Related Notes

- Architecture Overview: [[00-Brain-Overview]]
- Core Generator Subsystem: [[03-Core-LLM-Generator]]
- GGUF Quantization Step: [[GGUF-Quantization]]
- Multi-Guild Dataset: [[Multi-Guild-Train]]
