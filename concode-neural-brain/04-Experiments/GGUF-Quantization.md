---
title: GGUF Quantization & Metal GPU Pipeline
type: experiment
tags:
  - experiment/gguf
  - quantization/q4km
  - hardware/metal
  - llamacpp/mac
precision: Q4_K_M
file_size: 4.0 GB
code_file: src/convert_to_gguf.sh
---

# GGUF Quantization & Metal GPU Pipeline

> Conversion pipeline converting 16-bit HuggingFace models into quantized GGUF format (`Q4_K_M`) for local execution on Apple Silicon via Metal GPU.

---

## Quantization Strategy

To execute a 7-billion parameter model smoothly on Apple Silicon MacBooks without requiring massive VRAM, the merged 16-bit float model is quantized using `llama.cpp`:

| Quantization Type | Size | Quality / Loss | Target Use Case |
|-------------------|------|----------------|-----------------|
| **FP16 (Unquantized)** | ~13.5 GB | Lossless | Baseline reference |
| **Q8_0** | ~7.1 GB | Near-Lossless | High VRAM Macs |
| **Q5_K_M** | ~4.7 GB | High Quality | 16GB Macs |
| **Q4_K_M (Active)** | **~4.0 GB** | **Optimal Balance** | **Standard Apple Silicon** |

---

## Pipeline Commands (`src/convert_to_gguf.sh`)

```bash
# 1. Build llama.cpp with Apple Metal support
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make GGML_METAL=1 -j$(sysctl -n hw.ncpu)

# 2. Convert HuggingFace merged weights to F16 GGUF
python3 convert_hf_to_gguf.py \
    ../models/codellama-7b-concode-merged \
    --outfile ../models/codellama-7b-concode.f16.gguf \
    --outtype f16

# 3. Quantize F16 to Q4_K_M (~4 GB)
./llama-quantize \
    ../models/codellama-7b-concode.f16.gguf \
    ../models/codellama-7b-concode.Q4_K_M.gguf \
    Q4_K_M
```

---

## Related Notes

- Fine-Tuning Step: [[QLoRA-FineTuning]]
- Core Generator Subsystem: [[03-Core-LLM-Generator]]
- Master Dashboard: [[Dashboard]]
