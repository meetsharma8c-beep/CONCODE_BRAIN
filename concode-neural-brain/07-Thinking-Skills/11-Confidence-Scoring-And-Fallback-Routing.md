---
title: Thinking Skill — Confidence Scoring & Fallback Routing
type: thinking_skill
tags:
  - skill/confidence-scoring
  - routing/fallback
---

# Thinking Skill: Confidence Scoring & Fallback Routing

> Evaluates classification confidence scores and routes low-confidence requests through deterministic fallback pipelines.

---

## Decision Logic

```
If Softmax Confidence >= 0.70:
   Route to Neural Guild Pathway
Else:
   Route to Fallback Generalist (Fullstack Guild) + Keyword Heuristics
```

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/01-Intent-Classifier|01-Intent-Classifier]]
