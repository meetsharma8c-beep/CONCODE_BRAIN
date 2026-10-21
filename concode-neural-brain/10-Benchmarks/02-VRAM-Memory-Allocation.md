---
title: Benchmark — VRAM Memory Allocation
type: benchmark
tags:
  - benchmark/memory
  - memory/vram
---

# Benchmark: VRAM Memory Allocation

> Memory allocation breakdown for base models, quantization formats, and KV-cache buffers on Apple Silicon.

---

## Memory Footprint Table

| Component | Precision / Format | Memory Allocation (MB) | Location |
|-----------|--------------------|------------------------|----------|
| **CodeLlama-7B Model Weights** | Q4_K_M 4-bit Quantization | 3,800 MB | Metal GPU Unified RAM |
| **KV-Cache Tensor Buffer** | FP16 (2048 Context Length) | 1,070 MB | Metal GPU Unified RAM |
| **DistilBERT Intent Model** | FP32 PyTorch Tensor | 260 MB | System RAM |
| **MiniLM Embedding Model** | FP32 PyTorch Tensor | 90 MB | System RAM |
| **FAISS Vector Search Index** | Flat IP 384D | 15 MB | System RAM |
| **CodeT5 Repair Model** | FP32 PyTorch Tensor | 240 MB | System RAM |
| **Total Memory Allocation** | Combined Footprint | **5,475 MB (~5.5 GB)** | **Unified Memory** |

---

## Related Notes

- MOC: [[10-Benchmarks/Benchmarks-MOC|Benchmarks-MOC]]
- Master Dashboard: [[00-Dashboard/Dashboard|Dashboard]]
