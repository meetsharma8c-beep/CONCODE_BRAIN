---
title: Thinking Skill — Pydantic Request Schema Validation
type: thinking_skill
tags:
  - skill/pydantic-validation
  - api/schema
---

# Thinking Skill: Pydantic Request Schema Validation

> Validates HTTP POST request payload schemas against strict Pydantic model definitions prior to neural processing.

---

## Schema Definition

```python
class CognitiveRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User prompt text")
    session_id: Optional[str] = Field(None, description="UUID session identifier")
    workspace_files: Optional[Dict[str, str]] = Field(default_factory=dict)
```

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/06-FastAPI-Service|06-FastAPI-Service]]
