---
title: Thinking Skill — OpenAPI Swagger Schema Generation
type: thinking_skill
tags:
  - skill/openapi-schema
  - api/documentation
---

# Thinking Skill: OpenAPI Swagger Schema Generation

> Auto-generates OpenAPI 3.0 JSON specification and renders interactive Swagger UI at `/docs`.

---

## Schema Generation Sequence

1. Reflects endpoint method signatures and Pydantic models.
2. Constructs JSON Schema objects for inputs/outputs.
3. Serves interactive web documentation UI at `http://localhost:8000/docs`.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/06-FastAPI-Service|06-FastAPI-Service]]
