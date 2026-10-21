---
title: Decision Graph — Model Quantization Pipeline
type: decision_graph
tags:
  - graph/quantization
  - decision/gguf-pipeline
---

# Decision Graph: Model Quantization Pipeline

> Process graph for converting FP16 PyTorch model weights into Metal GPU-optimized GGUF files.

---

## Flowchart Graph

```mermaid
graph TD
    Start[Colab QLoRA Fine-Tuned Adapter] --> Merge[Merge Adapter into Base CodeLlama-7B FP16]
    Merge --> ExportFP16[Export Merged Model to PyTorch FP16]
    
    ExportFP16 --> ConvertGGUF[Run convert_hf_to_gguf.py]
    ConvertGGUF --> OutFP16GGUF[Output codellama-7b-concode.f16.gguf]
    
    OutFP16GGUF --> Quantize[Run llama-quantize Q4_K_M]
    Quantize --> FinalGGUF[Output codellama-7b-concode.Q4_K_M.gguf]
    
    FinalGGUF --> DeployMetal[Deploy to models/ directory for Metal GPU]
```

---

## Related Notes

- MOC: [[08-Decision-Graphs/Decision-Graphs-MOC|Decision-Graphs-MOC]]
- Quantization Experiment: [[04-Experiments/GGUF-Quantization|GGUF-Quantization]]
