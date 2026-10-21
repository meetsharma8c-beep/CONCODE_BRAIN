---
title: Benchmark — Inference Latency Breakdown
type: benchmark
tags:
  - benchmark/latency
  - performance/subsystems
---

# Benchmark: Inference Latency Breakdown

> Measured execution latency across the 5 neural subsystems on Apple Silicon (M1/M2/M3 Metal GPU).

---

## Subsystem Latency Table

| Subsystem | Underlying Technology | Mean Latency (ms) | % of Total Pipeline |
|-----------|------------------------|-------------------|---------------------|
| **1. Intent Classifier** | DistilBERT / Keywords | 8.5 ms | 0.5% |
| **2. Workspace Retriever** | MiniLM + FAISS | 18.2 ms | 1.0% |
| **3. Core LLM Generator** | CodeLlama-7B (Q4_K_M) | 1,780.0 ms | 95.6% |
| **4. Code Repairer** | CodeT5 / Regex Balancer | 42.1 ms | 2.3% |
| **5. Session Memory** | In-Memory Store | 1.2 ms | 0.1% |
| **Total Pipeline** | Full End-to-End | **1,850.0 ms** | **100.0%** |

---

## Related Notes

- MOC: [[10-Benchmarks/Benchmarks-MOC|Benchmarks-MOC]]
- Master Dashboard: [[00-Dashboard/Dashboard|Dashboard]]
