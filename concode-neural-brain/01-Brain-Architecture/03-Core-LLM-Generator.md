---
title: Subsystem 3 — Core LLM Generator
type: subsystem
tags:
  - subsystem/generator
  - model/codellama
  - hardware/metal
  - lora/adapters
subsystem_number: 3
model: CodeLlama-7B-Instruct (GGUF Q4_K_M)
parameters: 6,738,415,616
code_file: src/brain/generator.py
---

# Subsystem 3: Core LLM Generator

> **CodeLlama-7B Quantized GGUF (`Q4_K_M`)** executed via `llama-cpp-python` with **Apple Metal GPU acceleration**.

---

## Overview

The **Core LLM Generator** is the neural backbone of the CONCODE Neural Brain. It contains 7 billion+ parameters across 32 transformer layers, executing code generation tailored to system prompts provided by the 11 [[Guild-Overview|Expert Guilds]].

- **File Source**: [`src/brain/generator.py`](file:///Users/ms/Desktop/CONCODE_BRAIN/src/brain/generator.py)
- **Class**: `CodeGenerator`
- **Base Model**: CodeLlama-7B-Instruct
- **Quantization**: `Q4_K_M` (GGUF format, ~4.0 GB)
- **GPU Acceleration**: Apple Metal GPU (`n_gpu_layers=99` offloads all 32 layers)
- **Context Length**: 4,096 tokens
- **Threads**: 6 (optimized for Apple Silicon performance cores)

---

## Model Specifications & Parameter Breakdown

| Component | Shape | Parameters | Function |
|-----------|-------|------------|----------|
| **Token Embedding** | `(32016, 4096)` | 131,137,536 | Maps vocabulary tokens to 4D vector space |
| **Attention Projections (×32)** | `q, k, v, o (4096, 4096)` | 2,147,483,648 | Multi-head attention across 32 heads |
| **SwiGLU FFN Layers (×32)** | `gate, up, down (4096, 11008)` | 4,328,521,728 | Feed-forward projection & feature extraction |
| **RMSNorm Layers (×65)** | `(4096,)` | 266,240 | Layer normalization pre-attention/FFN |
| **LM Head Output** | `(4096, 32016)` | 131,137,536 | Maps hidden state back to vocabulary logits |
| **TOTAL PARAMETERS** | — | **6,738,415,616** | **~6.74 Billion Parameters** |

---

## Prompt Formatting (`_build_prompt`)

Generates instruction-tuned prompts following the standard CodeLlama instruct format:

```text
<s>[INST] <<SYS>>
You are CONCODE Debugger — an elite debugging specialist...

### Relevant Workspace Code (use as reference):
```
// --- src/auth.js ---
function login() { ... }
```
<</SYS>>

Fix the null pointer crash in login() [/INST] 
```

---

## Hardware & Inference Settings

- **GPU Offload**: `n_gpu_layers=99` (forces llama.cpp to allocate all layers to Apple Metal VRAM)
- **Temperature**: `0.3` (low temperature for deterministic code output)
- **Top P**: `0.9` (Nucleus sampling threshold)
- **Stop Tokens**: `["</s>", "[INST]"]`

---

## Related Notes

- Architecture Overview: [[00-Brain-Overview]]
- Previous Pipeline Step: [[02-Workspace-Retriever]]
- Next Pipeline Step: [[04-Code-Repairer]]
- Fine-Tuning Details: [[QLoRA-FineTuning]]
- Quantization Guide: [[GGUF-Quantization]]
