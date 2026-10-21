---
title: FastAPI Service & Cognitive API
type: service
tags:
  - api/fastapi
  - server/cognitive
  - endpoint/pipeline
host: 0.0.0.0
port: 8000
code_file: src/service.py
---

# FastAPI Service & Cognitive Engine API

> Central FastAPI server orchestrating the 5 subsystems and exposing the main cognitive endpoint `POST /api/v1/cognitive`.

---

## Overview

The **FastAPI Service** serves as the API gateway and coordinator for all neural subsystems. It accepts natural language queries and workspace file contents, passes them through intent classification, retrieval, LLM generation, and code repair, and returns structured JSON responses to the client.

- **File Source**: [`src/service.py`](file:///Users/ms/Desktop/CONCODE_BRAIN/src/service.py)
- **Framework**: FastAPI + Uvicorn
- **Default Port**: `8000`
- **CORS Policy**: Permissive (`*`) allowing cross-origin requests from web editors.

---

## API Endpoints

### 1. Main Cognitive Pipeline
`POST /api/v1/cognitive`

**Request Body (`CognitiveRequest`):**
```json
{
  "query": "Fix the null pointer bug in my login form",
  "workspace_files": {
    "login.js": "function login() { const user = null; return user.name; }"
  },
  "session_id": "optional-uuid-string",
  "mode": "text"
}
```

**Response Body (`CognitiveResponse`):**
```json
{
  "code": "function login() {\n  const user = null;\n  if (!user) return null;\n  return user.name;\n}",
  "guild": "debugger",
  "guild_icon": "",
  "confidence": 0.95,
  "repair_applied": true,
  "session_id": "b3e94a11-8f2b-4e69-921a-7952a10b4291",
  "subsystems": {
    "intent": "keyword_fallback",
    "retriever": "indexed_1_files",
    "generator": "fallback",
    "repair": "regex_fallback"
  },
  "latency_ms": 14.82
}
```

---

### 2. Utility & Health Endpoints

- `GET /`: Basic service metadata and subsystem load status.
- `GET /health`: Healthcheck endpoint (`{"status": "healthy"}`).
- `GET /api/v1/guilds`: List all 11 expert guilds, icons, keywords, and system prompts.
- `GET /api/v1/status`: Comprehensive status report of loaded models, active sessions, and GPU flags.

---

## Related Notes

- Architecture Overview: [[00-Brain-Overview]]
- Client Integration Script: [[07-Client-Integration]]
- Master Dashboard: [[Dashboard]]
