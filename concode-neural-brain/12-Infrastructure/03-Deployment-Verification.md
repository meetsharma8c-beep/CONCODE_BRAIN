---
title: Infrastructure — Deployment Verification
type: infrastructure
tags:
  - infra/deployment
  - status/completed
  - hardware/apple-silicon
date: 2026-08-16
---

# Infrastructure: Deployment Verification

> Verification report for model fine-tuning, GGUF model conversion, MPS Metal GPU acceleration, and service deployment.

---

## 1. Fine-Tuning & Quantization Summary

- **Base Model**: CodeLlama-7B-Instruct (4-bit BNB base)
- **Adapter Fine-Tuning**: QLoRA with rank $r=64$, $\alpha=128$ across 224 projection matrices
- **Local Intent Classification**: DistilBERT sequence classifier (13 intent classes)
- **Local Code Repair**: CodeT5-small model fine-tuned on structural syntax pairs
- **Inference Packaging**: Merged float16 model quantized to Q4_K_M GGUF format (~4.0 GB)

---

## 2. Hardware & Acceleration Stack

- **Target Engine**: PyTorch 2.0+ Metal Performance Shaders (`mps`) backend
- **CPU Vectorization**: Apple Accelerate and BNNS Framework integration
- **Llama Metal Binding**: `llama-cpp-python` compiled with `LLAMA_METAL=1` flag
- **Layer Offloading**: 100% layer execution offloaded to Apple Silicon GPU cores

---

## 3. Operational Deployment Checklist

- [x] DistilBERT Intent Classifier trained and saved to `models/intent_classifier/`
- [x] CodeT5 Code Repairer trained and saved to `models/code_repair/`
- [x] Base model LoRA adapters merged into float16 export
- [x] GGUF conversion script `src/convert_to_gguf.sh` executed
- [x] Hardware verification confirmed MPS and Metal GPU acceleration active
- [x] FastAPI Service endpoint `src/service.py` configured for inference

---

## 4. Related Notes

- Apple Silicon Setup: [[12-Infrastructure/02-Apple-Silicon-Metal-Setup|02-Apple-Silicon-Metal-Setup]]
- QLoRA Fine-Tuning: [[04-Experiments/QLoRA-FineTuning|QLoRA-FineTuning]]
- GGUF Quantization: [[04-Experiments/GGUF-Quantization|GGUF-Quantization]]
- Dashboard: [[00-Dashboard/Dashboard|Dashboard]]
