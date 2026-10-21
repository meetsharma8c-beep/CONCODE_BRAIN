---
title: Intent Classifier Training Dataset
type: dataset
tags:
  - dataset/intent
  - distilbert/data
  - classification/jsonl
dataset_file: data/intent_dataset.jsonl
record_count: 5500
file_size: 422 KB
---

# Intent Classifier Dataset (`intent_dataset.jsonl`)

> **5,500 labeled prompt examples** distributed evenly across the 11 [[Guild-Overview|Expert Guilds]] (500 examples per class).

---

## Dataset Overview

- **File Source**: [`data/intent_dataset.jsonl`](file:///Users/ms/Desktop/CONCODE_BRAIN/data/intent_dataset.jsonl)
- **Target Model**: DistilBERT sequence classifier ([[01-Intent-Classifier]])
- **Classes**: 11 (`debugger`, `webgl`, `ai_ml`, `qa`, `security`, `performance`, `database`, `ui_ux`, `devops`, `api`, `fullstack`)
- **Class Balance**: 500 prompts per class (100% balanced)

---

## Record Schema Example

```json
{"text": "Why am I getting Uncaught TypeError: Cannot read property 'map' of undefined?", "label": "debugger"}
{"text": "Create a GLSL fragment shader for a glowing plasma sphere in Three.js", "label": "webgl"}
{"text": "How do I implement JWT token refresh flow in FastAPI?", "label": "security"}
```

---

## Related Notes

- Generation Script: [[Data-Pipeline]]
- Subsystem 1: [[01-Intent-Classifier]]
- Guild Index: [[Guild-Overview]]
