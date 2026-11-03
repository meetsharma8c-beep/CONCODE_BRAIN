---
title: Decision Graph -- 3-Tier Hybrid Compute Router
type: decision_graph
tags:
  - decision/router
  - graph/compute
---

# Decision Graph: 3-Tier Hybrid Compute Router

```mermaid
flowchart TD
    Task["Incoming Task + Workspace + Active Guilds"] --> Score["Compute Complexity Score C in [0.0, 1.0]"]
    Score --> CheckTier{"Evaluate Score C"}
    CheckTier -->|"C < 0.40"| Tier1["TIER_1_REFLEX (Fast Local 7B)"]
    CheckTier -->|"0.40 <= C < 0.75"| Tier2["TIER_2_DEEP_LOCAL (Multi-Step Metal Reasoning)"]
    CheckTier -->|"C >= 0.75"| CheckSec{"Secondary Frontier Configured?"}
    CheckSec -->|Yes| Tier3["TIER_3_FRONTIER (Remote High-Capacity Engine)"]
    CheckSec -->|No| Tier2
    Tier1 --> PrimaryRun{"Primary Execution Succeeded?"}
    Tier2 --> PrimaryRun
    PrimaryRun -->|Yes| Return["Return Verified Output"]
    PrimaryRun -->|No| Escalate["Automatic Fallback Escalation to Secondary Engine"]
    Escalate --> Return
```

---

## Related Notes

- Decision Graphs MOC: [[08-Decision-Graphs/Decision-Graphs-MOC|Decision-Graphs-MOC]]
- Router Subsystem: [[01-Brain-Architecture/16-Hybrid-Compute-Router|16-Hybrid-Compute-Router]]
