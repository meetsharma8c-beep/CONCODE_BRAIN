---
title: Thinking Skill — CORS Security & Origin Validation
type: thinking_skill
tags:
  - skill/cors-security
  - api/fastapi
code_file: src/service.py
---

# Thinking Skill: CORS Security & Origin Validation

> Handles Cross-Origin Resource Sharing (CORS) preflight validation for web agency frontends connecting to local brain server.

---

## Preflight Verification Sequence

1. `OPTIONS` Request → Evaluates `Access-Control-Allow-Origin`.
2. Verifies allowed methods (`POST`, `GET`, `OPTIONS`).
3. Responds with status 200 and origin permission headers.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/06-FastAPI-Service|06-FastAPI-Service]]
