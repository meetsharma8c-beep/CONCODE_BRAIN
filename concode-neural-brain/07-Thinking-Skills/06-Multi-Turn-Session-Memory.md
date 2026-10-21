---
title: Thinking Skill — Multi-Turn Session Memory
type: thinking_skill
tags:
  - skill/session-memory
  - memory/stateful
code_file: src/service.py
---

# Thinking Skill: Multi-Turn Session Memory

> Manages stateful conversational history per session UUID for context-aware multi-turn dialog.

---

## Mechanism & Math

- Maintains sliding window of last 3 turns (6 messages: 3 `user`, 3 `assistant`).
- Trims memory queue dynamically to fit context length constraints ($n_{\text{ctx}} = 4096$).

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/05-Session-Memory|05-Session-Memory]]
