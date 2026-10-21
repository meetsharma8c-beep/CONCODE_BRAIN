---
title: Thinking Skill — System Prompt Role Injection
type: thinking_skill
tags:
  - skill/system-prompting
  - llama/instruct
code_file: src/brain/generator.py
---

# Thinking Skill: System Prompt Role Injection

> Injects specialized expert guild system prompts into CodeLlama-7B instruct token boundaries.

---

## Token Formatting Template

```
[INST] <<SYS>>
You are {guild_name} — an elite technical specialist.
{guild_system_prompt}
<</SYS>>

Context:
{workspace_retrieved_code}

User Query:
{user_query} [/INST]
```

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/03-Core-LLM-Generator|03-Core-LLM-Generator]]
- Guild Index: [[02-Guilds/Guild-Overview|Guild-Overview]]
