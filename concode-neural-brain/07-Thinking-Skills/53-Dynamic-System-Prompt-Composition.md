---
title: Thinking Skill -- Dynamic System Prompt Composition
type: thinking_skill
tags:
  - skill/dynamic-prompt
  - social/prompt-building
---

# Thinking Skill: Dynamic System Prompt Composition

> Replaces static guild system prompts with context-aware compositions that incorporate sentiment adaptation, user profile personalization, topic awareness, error history, and conversation continuity -- all capped within a ~450 token budget.

---

## Composition Layers

The prompt is assembled from 6 sequential layers, each appended only when relevant:

| Layer | Condition | Purpose |
|-------|-----------|---------|
| **1. Guild Base** | Always | Core guild persona and domain expertise (truncated at 600 chars) |
| **2. Tone Adaptation** | Always | Casual or formal language directive based on user profile |
| **3. User Personalization** | If `name` exists | Address user by name for rapport |
| **4. Sentiment Instructions** | If not `neutral` | Empathetic phrasing for frustrated; step-by-step for confused; energetic for positive |
| **5. Topic Awareness** | If total queries > 3 | Notes the user's most activated guild domain |
| **6. Error Awareness** | If >= 3 repairs | Adds extra syntax correctness directive |
| **7. History Summary** | If history exists | Compact prior conversation context |

---

## Token Budget Enforcement

$$\text{Max Chars} = 450 \times 4 = 1800$$

If the assembled prompt exceeds the character limit, it is truncated with an ellipsis to stay within the context window allocation.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/09-Social-Intelligence|09-Social-Intelligence]]
