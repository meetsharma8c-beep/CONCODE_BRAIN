---
title: Thinking Skill -- Episodic Experience Replay And SHA256 Caching
type: thinking_skill
tags:
  - skill/episodic-memory
  - subsystem/memory
---

# Thinking Skill: Episodic Experience Replay And SHA256 Caching

> Recalls past verified problem-solving episodes using Critic-weighted Jaccard similarity and skips redundant workspace re-indexing via content-addressable SHA-256 digests.

---

## Episodic Recall Scoring

Given query token set $T_q$ and past verified episode token set $T_e$ with Critic score $S_e \in [0, 1]$:

$$
\text{Sim}(q, e) = \frac{|T_q \cap T_e|}{|T_q \cup T_e|} \cdot (0.7 + 0.3 \cdot S_e)
$$

Top-$K$ episodes exceeding $\text{Sim}(q, e) \ge 0.15$ are formatted into the prompt as Few-Shot Experience Replay.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/15-Cognitive-Memory-Manager|15-Cognitive-Memory-Manager]]
