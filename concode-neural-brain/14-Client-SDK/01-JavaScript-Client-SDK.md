---
title: Client SDK — JavaScript Client SDK
type: client_sdk
tags:
  - sdk/javascript
  - client/browser
code_file: integration/concode_brain_client.js
---

# Client SDK: JavaScript Client SDK

> Lightweight ES6 browser wrapper for calling CONCODE Neural Brain endpoints (`http://localhost:8000`).

---

## Client API Reference

```javascript
class ConcodeBrain {
  static async query(prompt, options = {}) {
    const res = await fetch('http://localhost:8000/api/v1/cognitive', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: prompt, ...options })
    });
    return await res.json();
  }
}
```

---

## Related Notes

- MOC: [[14-Client-SDK/Client-SDK-MOC|Client-SDK-MOC]]
- Subsystem: [[01-Brain-Architecture/07-Client-Integration|07-Client-Integration]]
