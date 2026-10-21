---
title: Diagnostic Playbook — Model Load Failure Recovery
type: diagnostic_playbook
tags:
  - diagnostic/model-load
  - recovery/fallback
---

# Diagnostic Playbook: Model Load Failure Recovery

> Self-healing recovery steps when `codellama-7b-concode.Q4_K_M.gguf` is missing or corrupted.

---

## Symptom

Terminal log warning: `WARNING: Model file not found at models/codellama-7b-concode.Q4_K_M.gguf`.

---

## Recovery Steps

1. Verify server activates **Fallback Heuristic Mode** (`"generator": false` in `GET /`).
2. Run GGUF conversion script: `chmod +x src/convert_to_gguf.sh && ./src/convert_to_gguf.sh`.
3. Verify Uvicorn hot-reloads and initializes neural generator.

---

## Related Notes

- MOC: [[15-Diagnostics/Diagnostics-MOC|Diagnostics-MOC]]
- Subsystem: [[01-Brain-Architecture/03-Core-LLM-Generator|03-Core-LLM-Generator]]
