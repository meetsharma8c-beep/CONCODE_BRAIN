---
title: Thinking Skill — Multi-Turn Conversation Context Trimming
type: thinking_skill
tags:
  - skill/context-trimming
  - memory/sliding-window
---

# Thinking Skill: Multi-Turn Conversation Context Trimming

> Enforces sliding window constraints on conversation history to maintain token context length limits.

---

## Window Trimming Algorithm

$$\text{History}_{\text{trimmed}} = \text{History}[-6:] = [u_1, a_1, u_2, a_2, u_3, a_3]$$

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/05-Session-Memory|05-Session-Memory]]
