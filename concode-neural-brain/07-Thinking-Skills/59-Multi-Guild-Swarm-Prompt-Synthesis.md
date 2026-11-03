---
title: Thinking Skill -- Multi-Guild Swarm Prompt Synthesis
type: thinking_skill
tags:
  - skill/swarm-synthesis
  - subsystem/swarm
---

# Thinking Skill: Multi-Guild Swarm Prompt Synthesis

> Activates up to $K$ expert guilds simultaneously via hybrid neural-keyword probability scoring and composes a unified multi-specialist system prompt.

---

## Multi-Guild Scoring

1. Compute primary guild prediction $(g_1, c_1)$ via `IntentClassifier.predict(query)`.
2. Score all 18 guilds over domain keyword density and DistilBERT softmax probabilities $P(g_i \mid x)$.
3. Retain top-$K$ guilds where $\max(P_{\text{neural}}(g_i), S_{\text{keyword}}(g_i)) \ge \tau_{\text{min}}$.
4. Compose the lead guild's full system persona with supporting guild constraint directives.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/14-Multi-Guild-Swarm|14-Multi-Guild-Swarm]]
