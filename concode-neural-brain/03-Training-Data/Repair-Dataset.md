---
title: Code Repair Training Dataset
type: dataset
tags:
  - dataset/repair
  - codet5/data
  - self-healing/data
dataset_file: data/repair_dataset.jsonl
record_count: 10000
file_size: 4.17 MB
---

# Code Repair Dataset (`repair_dataset.jsonl`)

> **10,000 paired code examples** containing synthetic syntax errors, broken bracket structures, and typos mapped to fixed code outputs.

---

## Dataset Overview

- **File Source**: [`data/repair_dataset.jsonl`](file:///Users/ms/Desktop/CONCODE_BRAIN/data/repair_dataset.jsonl)
- **Target Model**: CodeT5-small Seq2Seq model ([[04-Code-Repairer]])
- **Volume**: 10,000 paired records
- **Task Format**: `broken` → `fixed`

---

## Schema Example

```json
{
  "broken": "functoin calculateTotal(price, tax) {\n  retun price * (1 + tax);\n",
  "fixed": "function calculateTotal(price, tax) {\n  return price * (1 + tax);\n}"
}
```

---

## Related Notes

- Data Pipeline: [[Data-Pipeline]]
- Subsystem 4 (Code Repairer): [[04-Code-Repairer]]
- Debugger Guild: [[Debugger-Guild]]
