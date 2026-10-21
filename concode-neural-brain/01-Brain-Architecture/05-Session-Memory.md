---
title: Subsystem 5 — Session Memory
type: subsystem
tags:
  - subsystem/session
  - memory/in-memory
  - conversation/history
subsystem_number: 5
storage: In-memory dictionary
max_turns: 3
code_file: src/service.py
---

# Subsystem 5: Session Memory

> **Stateful in-memory conversation store** providing multi-turn context awareness to the cognitive engine.

---

## Overview

The **Session Memory** subsystem retains previous conversation turns per session UUID. This allows users to ask follow-up questions (e.g. *"Now add tests for this function"*) without re-pasting prior context.

- **File Source**: [`src/service.py`](file:///Users/ms/Desktop/CONCODE_BRAIN/src/service.py#L85)
- **Data Structure**: `defaultdict(list)` mapping `session_id` → `List[Dict[str, str]]`
- **History Boundary**: Keeps the last **3 conversation turns** (up to 6 message objects: 3 `user`, 3 `assistant`)

---

## Workflow & Data Structures

```mermaid
graph TD
    Req[Incoming Request with session_id] --> CheckStore{Session exists in session_store?}
    CheckStore -- Yes --> FetchHistory[Fetch last 6 messages]
    CheckStore -- No --> NewSession[Generate UUID session_id]
    
    FetchHistory --> FormatPrompt[Format into CodeLlama Instruct Prompt]
    NewSession --> FormatPrompt

    FormatPrompt --> Pipeline[Execute Neural Brain Pipeline]
    Pipeline --> NewResponse[Generated Response]

    NewResponse --> AppendStore[Append User Prompt & Assistant Response to session_store]
    AppendStore --> TrimStore[Trim session_store to last 6 entries]
```

---

## Message Schema Example

```json
{
  "session_id": "b3e94a11-8f2b-4e69-921a-7952a10b4291",
  "history": [
    {
      "role": "user",
      "content": "Create a FastAPI endpoint for user login."
    },
    {
      "role": "assistant",
      "content": "@app.post('/login')\nasync def login(credentials: UserCredentials): ..."
    },
    {
      "role": "user",
      "content": "Now add JWT authentication middleware to it."
    }
  ]
}
```

---

## Related Notes

- Architecture Overview: [[00-Brain-Overview]]
- Generator Formatting: [[03-Core-LLM-Generator]]
- Service Handler: [[06-FastAPI-Service]]
- Client Integration: [[07-Client-Integration]]
- Session Logs: [[Session-Tracking]]
