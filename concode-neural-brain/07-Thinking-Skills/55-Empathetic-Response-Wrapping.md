---
title: Thinking Skill -- Empathetic Response Wrapping
type: thinking_skill
tags:
  - skill/empathetic-wrapping
  - social/empathy
---

# Thinking Skill: Empathetic Response Wrapping

> Wraps generated code output with sentiment-keyed human-like messages, selected randomly from template pools for natural variation. Adds repair notices when the code self-healing subsystem modifies the output.

---

## Template Selection Logic

```
If sentiment == "negative":
    Select phrase from frustration pool (8 variants)
If sentiment == "confused":
    Select phrase from confusion pool (7 variants)
If sentiment == "positive":
    Select phrase from success pool (6 variants)
Else:
    Select phrase from neutral pool (4 variants)

If repair_applied:
    Append phrase from repair_notice pool (4 variants)
```

---

## Output Assembly

| Sentiment | Output Format |
|-----------|---------------|
| `negative` or `confused` | Empathetic message + blank line + code |
| `positive` or `neutral` | Code only (message returned separately in API) |

The `personalized_message` field is always returned in the API response regardless of whether it is prepended to the code output.

---

## Template Categories

| Category | Phrase Count | Trigger |
|----------|:----------:|---------|
| `frustration` | 8 | Negative sentiment detected |
| `confusion` | 7 | Confused sentiment detected |
| `success` | 6 | Positive sentiment detected |
| `apology` | 4 | Self-correction scenarios |
| `encouragement` | 5 | Progress acknowledgment |
| `greeting` | 4 | Session initialization |
| `repair_notice` | 4 | Code repair subsystem activated |
| `neutral` | 4 | Default / neutral sentiment |

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/09-Social-Intelligence|09-Social-Intelligence]]
