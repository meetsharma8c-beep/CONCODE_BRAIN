---
title: Thinking Skill — HTTP Status Code Error Mapping
type: thinking_skill
tags:
  - skill/http-error-mapping
  - api/fastapi
---

# Thinking Skill: HTTP Status Code Error Mapping

> Maps internal subsystem exceptions into structured JSON error payloads with standard HTTP status codes.

---

## Status Mapping Table

| Status Code | Exception Type | Payload Detail |
|-------------|----------------|----------------|
| `400 Bad Request` | `ValidationError` | Invalid JSON input schema |
| `404 Not Found` | `GuildNotFound` | Specified guild persona unavailable |
| `500 Server Error` | `InferenceError` | Subsystem execution exception |

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/06-FastAPI-Service|06-FastAPI-Service]]
