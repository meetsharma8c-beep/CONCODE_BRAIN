---
title: Decision Graph — Query Guild Routing
type: decision_graph
tags:
  - graph/routing
  - decision/guild-selection
---

# Decision Graph: Query Guild Routing

> Logical decision tree determining how user prompts are routed to 1 of 13 expert guilds.

---

## Flowchart Graph

```mermaid
graph TD
    Start[User Query Received] --> Parse[Tokenize & Extract Keyword Tags]
    Parse --> CheckNeural[Neural Classifier Available?]
    
    CheckNeural -->|Yes| DistilBERT[Run DistilBERT Classifier]
    CheckNeural -->|No| KeywordScore[Calculate Keyword Density Scores]
    
    DistilBERT --> EvalConf{Confidence >= 0.70?}
    KeywordScore --> EvalConf
    
    EvalConf -->|Yes| RouteSelected[Route to High-Confidence Guild]
    EvalConf -->|No| RouteFallback[Route to Fullstack Guild Default]
    
    RouteSelected --> InjectPrompt[Inject Guild System Prompt]
    RouteFallback --> InjectPrompt
```

---

## Related Notes

- MOC: [[08-Decision-Graphs/Decision-Graphs-MOC|Decision-Graphs-MOC]]
- Subsystem: [[01-Brain-Architecture/01-Intent-Classifier|01-Intent-Classifier]]
