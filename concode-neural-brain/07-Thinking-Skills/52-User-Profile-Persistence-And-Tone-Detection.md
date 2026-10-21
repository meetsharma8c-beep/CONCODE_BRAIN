---
title: Thinking Skill -- User Profile Persistence And Tone Detection
type: thinking_skill
tags:
  - skill/user-memory
  - social/tone-detection
---

# Thinking Skill: User Profile Persistence And Tone Detection

> Maintains persistent JSON-backed user profiles across sessions, tracking interaction history, guild activation frequency, error patterns, and automatically detecting the user's preferred communication tone from writing style signals.

---

## Profile Schema

| Field | Type | Retention | Purpose |
|-------|------|-----------|---------|
| `past_interactions` | List | Last 10 | Query/response pairs for pattern analysis |
| `favorite_topics` | Dict | Cumulative | Guild activation frequency counter |
| `common_errors` | List | Last 20 | Tracks queries where repair was applied |
| `sentiment_history` | List | Last 20 | Rolling sentiment label window |
| `tone` | String | Dynamic | Auto-detected: `casual` or `formal` |

---

## Tone Detection Scoring

$$
\text{Tone} =
\begin{cases}
\text{casual} & \text{if } S_{\text{casual}} > S_{\text{formal}} + 1 \\
\text{formal} & \text{if } S_{\text{formal}} > S_{\text{casual}} + 1 \\
\text{current} & \text{otherwise (preserve historical preference)}
\end{cases}
$$

**Casual signals**: exclamation marks (+2), slang/informal words (+3), emojis (+1), lowercase start (+1), contractions (+1).

**Formal signals**: sentence-ending punctuation (+1), polite phrasing (+2), uppercase start (+1), long sentences (+1).

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/09-Social-Intelligence|09-Social-Intelligence]]
