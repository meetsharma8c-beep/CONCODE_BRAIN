---
title: Multi-Guild Instruction Dataset
type: dataset
tags:
  - dataset/instruction
  - qlora/data
  - codellama/data
dataset_file: data/multi_guild_train.jsonl
record_count: 5500
file_size: 3.47 MB
---

# Multi-Guild Instruction Dataset (`multi_guild_train.jsonl`)

> **5,500 rich instruction-following pairs** formatted for QLoRA fine-tuning of CodeLlama-7B.

---

## Dataset Overview

- **File Source**: [`data/multi_guild_train.jsonl`](file:///Users/ms/Desktop/CONCODE_BRAIN/data/multi_guild_train.jsonl)
- **Target Model**: CodeLlama-7B-Instruct ([[01-Brain-Architecture/03-Core-LLM-Generator|03-Core-LLM-Generator]])
- **Fine-Tuning Method**: QLoRA (`r=64`, `α=128`) via Unsloth SFTTrainer ([[04-Experiments/QLoRA-FineTuning|QLoRA-FineTuning]])
- **Volume**: 5,500 samples (500 per guild)

---

## Formatted Instruction Schema

```json
{
  "system": "You are CONCODE Security — a cybersecurity and application security engineer...",
  "instruction": "Add password hashing using bcrypt in Node.js",
  "output": "const bcrypt = require('bcrypt');\n\nasync function hashPassword(password) {\n  const salt = await bcrypt.genSalt(10);\n  return await bcrypt.hash(password, salt);\n}"
}
```

Formatted during training into CodeLlama Instruct format:
`<s>[INST] <<SYS>>\n{system}\n<</SYS>>\n\n{instruction} [/INST] {output}</s>`

---

## Related Notes

- Data Generation Script: [[03-Training-Data/Data-Pipeline|Data-Pipeline]]
- Subsystem 3 (LLM Generator): [[01-Brain-Architecture/03-Core-LLM-Generator|03-Core-LLM-Generator]]
- Fine-Tuning Setup: [[04-Experiments/QLoRA-FineTuning|QLoRA-FineTuning]]
