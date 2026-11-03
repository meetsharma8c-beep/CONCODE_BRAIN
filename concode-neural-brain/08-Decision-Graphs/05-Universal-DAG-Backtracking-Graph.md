---
title: Decision Graph -- Universal DAG Planner & Backtracking
type: decision_graph
tags:
  - decision/planner
  - graph/dag
---

# Decision Graph: Universal DAG Planner & Backtracking

```mermaid
flowchart TD
    Goal["Incoming User Goal"] --> MultiIntent["IntentClassifier.predict_multi(top_k=3)"]
    MultiIntent --> Decompose["ExecutivePlanner.decompose()"]
    Decompose --> Validate{"validate_dag() Acyclic?"}
    Validate -->|No| FallbackPlan["Fallback Single-Node Plan"]
    Validate -->|Yes| ReadyQueue["Select ready_tasks() (in-degree == 0)"]
    FallbackPlan --> ReadyQueue
    ReadyQueue --> Execute["Execute Task via Swarm / CodingAgent"]
    Execute --> Critic{"Critic & Sandbox Gate Passed?"}
    Critic -->|Yes| MarkDone["mark_completed()"]
    MarkDone --> MoreTasks{"Remaining Tasks?"}
    MoreTasks -->|Yes| ReadyQueue
    MoreTasks -->|No| Harvest["Record Episodic Memory & Harvest Trajectory"]
    Critic -->|No| CanRetry{"attempts < max_attempts?"}
    CanRetry -->|Yes| Backtrack["State = BACKTRACKING (Inject Failure Feedback)"]
    Backtrack --> Execute
    CanRetry -->|No| MarkFailed["State = FAILED (Return Diagnostic Report)"]
```

---

## Related Notes

- Decision Graphs MOC: [[08-Decision-Graphs/Decision-Graphs-MOC|Decision-Graphs-MOC]]
- Planner Subsystem: [[01-Brain-Architecture/11-Executive-Meta-Planner|11-Executive-Meta-Planner]]
