---
title: Thinking Skill — LLM Generator Fallback Heuristics
type: thinking_skill
tags:
  - skill/fallback-generation
  - generator/fallback
---

# Thinking Skill: LLM Generator Fallback Heuristics

> Generates domain-specialized code skeletons when the 7B GGUF model is uninitialized or compiling.

---

## Fallback Template Structure

```python
# CONCODE Neural Brain — Model Not Loaded
# Detected Guild: {guild_name}
# System Prompt: {guild_system_prompt}
# Query: {user_query}
```

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/03-Core-LLM-Generator|03-Core-LLM-Generator]]
