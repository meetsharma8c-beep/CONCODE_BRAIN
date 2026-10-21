---
title: Benchmark — Code Repair Accuracy Metrics
type: benchmark
tags:
  - benchmark/accuracy
  - repair/metrics
---

# Benchmark: Code Repair Accuracy Metrics

> Evaluation metrics of CodeT5 neural repair and regex balancer over 10,000 synthetic syntax error test cases.

---

## Pass Rate Metrics

| Error Category | Pre-Repair AST Pass Rate | Post-Repair AST Pass Rate | Repair Lift |
|----------------|--------------------------|---------------------------|-------------|
| **Unclosed Brackets / Braces** | 12.4% | 98.7% | +86.3% |
| **Keyword Hallucinations** | 45.0% | 99.2% | +54.2% |
| **Null Access Safety** | 68.2% | 94.5% | +26.3% |
| **Combined Syntax Suite** | **41.8%** | **97.4%** | **+55.6%** |

---

## Related Notes

- MOC: [[10-Benchmarks/Benchmarks-MOC|Benchmarks-MOC]]
- Subsystem: [[01-Brain-Architecture/04-Code-Repairer|04-Code-Repairer]]
