---
title: Security Protocol — JWT Token Verification
type: security_protocol
tags:
  - protocol/jwt
  - security/auth
---

# Security Protocol: JWT Token Verification

> HMAC SHA-256 cryptographic verification of JWT bearer tokens protecting API endpoints.

---

## Token Verification Sequence

1. Extracts `Authorization: Bearer <token>` from HTTP headers.
2. Validates header signature using secret key $\mathbf{K}$:
   $$\text{Signature} = \text{HMAC-SHA256}(\text{header} + "." + \text{payload}, \mathbf{K})$$
3. Verifies token expiration timestamp (`exp > current_time`).

---

## Related Notes

- MOC: [[11-Security-Protocols/Security-Protocols-MOC|Security-Protocols-MOC]]
- Subsystem: [[01-Brain-Architecture/06-FastAPI-Service|06-FastAPI-Service]]
