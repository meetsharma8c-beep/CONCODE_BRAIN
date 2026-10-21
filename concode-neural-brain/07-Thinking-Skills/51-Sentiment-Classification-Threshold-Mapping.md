---
title: Thinking Skill -- Sentiment Classification Threshold Mapping
type: thinking_skill
tags:
  - skill/sentiment-mapping
  - social/sentiment
---

# Thinking Skill: Sentiment Classification Threshold Mapping

> Maps binary SST-2 model outputs (POSITIVE/NEGATIVE) into 4 nuanced sentiment classes using confidence threshold logic, with regex pattern overrides for confusion and frustration detection.

---

## Threshold Mapping Logic

$$
\text{Class}(x) =
\begin{cases}
\text{positive} & \text{if label} = \text{POS} \land \text{score} \geq 0.85 \\
\text{neutral} & \text{if label} = \text{POS} \land 0.55 \leq \text{score} < 0.85 \\
\text{negative} & \text{if label} = \text{NEG} \land \text{score} \geq 0.70 \\
\text{confused} & \text{if label} = \text{NEG} \land 0.50 \leq \text{score} < 0.70
\end{cases}
$$

---

## Pattern Override Layer

Before neural inference, two regex pattern banks are evaluated. If any pattern matches, it overrides the model output:

| Pattern Bank | Output Override | Example Triggers |
|-------------|-----------------|------------------|
| Confusion Patterns (10 regexes) | `confused` @ 0.80 | "I don't understand", "can you explain", "what does X mean" |
| Frustration Patterns (11 regexes) | `negative` @ 0.85 | "stuck for hours", "keeps failing", "not working", "give up" |

---

## Fallback Mechanism

When the DistilBERT model fails to load, a rule-based fallback counts negative and positive keyword matches and uses question mark frequency to estimate sentiment.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/09-Social-Intelligence|09-Social-Intelligence]]
