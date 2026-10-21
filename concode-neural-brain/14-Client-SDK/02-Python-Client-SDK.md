---
title: Client SDK -- Python Client SDK
type: client_sdk
tags:
  - sdk/python
  - client/server-side
---

# Client SDK: Python Client SDK

> Server-side Python wrapper for calling CONCODE Neural Brain endpoints from backend services and automation scripts.

---

## Client API Reference

```python
import httpx
from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class CognitiveResponse:
    code: str
    guild: str
    confidence: float
    repair_applied: bool
    session_id: str
    latency_ms: float

class ConcodeBrainClient:
    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-API-Key"] = api_key
        self.client = httpx.Client(base_url=base_url, headers=headers)

    def query(self, prompt: str, workspace_files: Optional[Dict[str, str]] = None,
              session_id: Optional[str] = None, mode: str = "code") -> CognitiveResponse:
        payload = {"query": prompt, "mode": mode}
        if workspace_files:
            payload["workspace_files"] = workspace_files
        if session_id:
            payload["session_id"] = session_id
        resp = self.client.post("/api/v1/cognitive", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return CognitiveResponse(**{k: data[k] for k in CognitiveResponse.__dataclass_fields__})

    def health(self) -> bool:
        return self.client.get("/health").status_code == 200
```

---

## Related Notes

- MOC: [[14-Client-SDK/Client-SDK-MOC|Client-SDK-MOC]]
- Subsystem: [[01-Brain-Architecture/07-Client-Integration|07-Client-Integration]]
- Protocol: [[11-Security-Protocols/04-API-Key-Validation|04-API-Key-Validation]]
