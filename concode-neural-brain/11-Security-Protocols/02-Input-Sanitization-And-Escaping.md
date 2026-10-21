---
title: Security Protocol — Input Sanitization & Escaping
type: security_protocol
tags:
  - protocol/sanitization
  - security/owasp
---

# Security Protocol: Input Sanitization & Escaping

> Escapes special control characters from incoming prompt strings to eliminate XSS, SQLi, and prompt injection attacks.

---

## Sanitization Strategy

- Replaces `<`, `>`, `&`, `"`, `'` with safe HTML entity escape sequences.
- Strips hidden shell control characters (`\x00`, `\x1b`).

---

## Related Notes

- MOC: [[11-Security-Protocols/Security-Protocols-MOC|Security-Protocols-MOC]]
- Subsystem: [[01-Brain-Architecture/06-FastAPI-Service|06-FastAPI-Service]]
