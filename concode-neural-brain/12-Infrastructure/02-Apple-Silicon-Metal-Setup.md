---
title: Infrastructure — Apple Silicon Metal Setup
type: infrastructure
tags:
  - infra/metal-gpu
  - hardware/apple-silicon
---

# Infrastructure: Apple Silicon Metal Setup

> Compilation flags and environment variables enabling Metal GPU hardware acceleration for llama-cpp-python.

---

## Build Environment Variables

```bash
export CMAKE_ARGS="-DLLAMA_METAL=on"
export FORCE_CMAKE=1
pip install llama-cpp-python --no-cache-dir --force-reinstall
```

- Offloads 100% of LLM transformer layers (`-ngl 99`) to Apple Metal GPU shaders.

---

## Related Notes

- MOC: [[12-Infrastructure/Infrastructure-MOC|Infrastructure-MOC]]
- Master Dashboard: [[00-Dashboard/Dashboard|Dashboard]]
