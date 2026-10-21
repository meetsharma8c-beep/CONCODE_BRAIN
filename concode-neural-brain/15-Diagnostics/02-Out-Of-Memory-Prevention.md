---
title: Diagnostic Playbook -- Out-of-Memory Prevention
type: diagnostic_playbook
tags:
  - diagnostic/oom
  - recovery/memory
---

# Diagnostic Playbook: Out-of-Memory Prevention

> Detection and recovery procedures when CodeLlama-7B GGUF inference exhausts available unified memory on Apple Silicon.

---

## Symptom

Process killed by macOS (`Killed: 9`) or Python `MemoryError` during model loading or generation. System memory pressure indicator transitions to critical (red) in Activity Monitor.

---

## Root Causes

| Cause | Trigger Condition |
|-------|-------------------|
| Excessive GPU layer offloading | `n_gpu_layers` exceeds available Metal VRAM headroom |
| Context window overflow | Input + generation exceeds `n_ctx` allocation (4096 tokens x 4096 hidden = ~64MB KV cache) |
| Concurrent model instances | Multiple Llama instances loaded simultaneously without cleanup |

---

## Prevention Steps

1. **Cap GPU layers**: Set `n_gpu_layers` to leave at least 2GB headroom below total unified memory.
2. **Enforce input length limits**: Truncate query + context to `n_ctx - max_tokens` before submission.
3. **Single-instance guard**: Verify no prior Llama instance exists before loading (`del` and `gc.collect()`).
4. **Monitor at startup**: Log `psutil.virtual_memory().available` and abort if below 4GB threshold.

---

## Recovery Steps

1. Restart the Uvicorn process: `./start.sh`.
2. Reduce `LLM_GPU_LAYERS` in `src/config.py` by 10 and retry.
3. If persistent, switch to a smaller quantization (Q3_K_S instead of Q4_K_M).

---

## Related Notes

- MOC: [[15-Diagnostics/Diagnostics-MOC|Diagnostics-MOC]]
- Subsystem: [[01-Brain-Architecture/03-Core-LLM-Generator|03-Core-LLM-Generator]]
- Thinking Skill: [[07-Thinking-Skills/41-Metal-GPU-Unified-Memory-Offloading|41-Metal-GPU-Unified-Memory-Offloading]]
