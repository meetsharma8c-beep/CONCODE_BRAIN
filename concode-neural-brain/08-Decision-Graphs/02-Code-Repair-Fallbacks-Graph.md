---
title: Decision Graph — Code Repair Fallbacks
type: decision_graph
tags:
  - graph/repair
  - decision/self-healing
---

# Decision Graph: Code Repair Fallbacks

> Decision tree governing sequential code repair passes across CodeT5 and regex heuristics.

---

## Flowchart Graph

```mermaid
graph TD
    Start[Raw LLM Generated Code] --> CheckSyntax{Passes AST Syntax Check?}
    
    CheckSyntax -->|Yes| ReturnClean[Return Unmodified Code]
    CheckSyntax -->|No| CheckNeuralRepair[CodeT5 Model Loaded?]
    
    CheckNeuralRepair -->|Yes| RunCodeT5[Run CodeT5 Beam Search Repair]
    CheckNeuralRepair -->|No| RunRegex[Run Stack Delimiter Balancer]
    
    RunCodeT5 --> VerifyCodeT5{AST Valid Now?}
    VerifyCodeT5 -->|Yes| SetRepairFlag[Set repair_applied = True]
    VerifyCodeT5 -->|No| RunRegex
    
    RunRegex --> SetRepairFlag
    SetRepairFlag --> ReturnClean
```

---

## Related Notes

- MOC: [[08-Decision-Graphs/Decision-Graphs-MOC|Decision-Graphs-MOC]]
- Subsystem: [[01-Brain-Architecture/04-Code-Repairer|04-Code-Repairer]]
