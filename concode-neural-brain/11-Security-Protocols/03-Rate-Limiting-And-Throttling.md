---
title: Security Protocol -- Rate Limiting & Throttling
type: security_protocol
tags:
  - protocol/rate-limit
  - security/abuse-prevention
---

# Security Protocol: Rate Limiting & Throttling

> Per-IP request throttling middleware to prevent API abuse, DDoS amplification, and GPU compute exhaustion.

---

## Throttling Strategy

1. Track request counts per client IP using a sliding window counter.
2. Enforce tiered limits:
   - `/api/v1/cognitive` (GPU-bound): 30 requests per minute per IP.
   - All other endpoints: 120 requests per minute per IP.
3. Return `HTTP 429 Too Many Requests` with `Retry-After` header when threshold is exceeded.

---

## Implementation Reference

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/cognitive")
@limiter.limit("30/minute")
async def cognitive(request: Request, body: CognitiveRequest):
    ...
```

---

## Related Notes

- MOC: [[11-Security-Protocols/Security-Protocols-MOC|Security-Protocols-MOC]]
- Subsystem: [[01-Brain-Architecture/06-FastAPI-Service|06-FastAPI-Service]]
