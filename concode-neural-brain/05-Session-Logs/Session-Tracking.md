---
title: Session Tracking & Latency Profiling
type: session_logs
tags:
  - session/tracking
  - latency/profiling
  - logs/metrics
---

# Session Tracking & Latency Profiling

> Multi-turn session state management and subsystem performance profiling metrics.

---

## Latency Breakdown per Request Step

| Step | Subsystem | Average Latency (ms) | Target Hardware |
|------|-----------|----------------------|-----------------|
| 1 | [[01-Intent-Classifier|Intent Classification]] | 8 – 15 ms | CPU / MPS |
| 2 | [[02-Workspace-Retriever|Workspace Retrieval & FAISS]] | 12 – 25 ms | CPU |
| 3 | [[03-Core-LLM-Generator|CodeLlama-7B Generation]] | 800 – 1800 ms | Apple Metal GPU |
| 4 | [[04-Code-Repairer|CodeT5 Neural Repair]] | 40 – 90 ms | CPU / MPS |
| **Total** | **End-to-End Pipeline** | **~900 – 1900 ms** | **Local Apple Silicon** |

---

## Related Notes

- Session Memory Subsystem: [[05-Session-Memory]]
- FastAPI Service: [[06-FastAPI-Service]]
- Master Dashboard: [[Dashboard]]
