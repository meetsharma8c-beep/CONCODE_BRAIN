---
title: Client SDK -- WebSocket Streaming Client
type: client_sdk
tags:
  - sdk/websocket
  - client/streaming
---

# Client SDK: WebSocket Streaming Client

> Persistent bidirectional connection for streaming token-by-token code generation responses from the neural brain.

---

## Protocol Design

1. Client opens WebSocket connection to `ws://localhost:8000/ws/cognitive`.
2. Client sends JSON message with `query`, `session_id`, and optional `workspace_files`.
3. Server streams response tokens as individual WebSocket text frames.
4. Server sends a final frame with `{"done": true, "guild": "...", "confidence": 0.95}` to signal completion.

---

## Client Reference (JavaScript)

```javascript
class ConcodeBrainStream {
  constructor(url = 'ws://localhost:8000/ws/cognitive') {
    this.url = url;
  }

  async *stream(prompt, options = {}) {
    const ws = new WebSocket(this.url);
    await new Promise((resolve, reject) => {
      ws.onopen = resolve;
      ws.onerror = reject;
    });
    ws.send(JSON.stringify({ query: prompt, ...options }));
    try {
      while (true) {
        const msg = await new Promise((resolve, reject) => {
          ws.onmessage = (e) => resolve(JSON.parse(e.data));
          ws.onerror = reject;
        });
        if (msg.done) return;
        yield msg.token;
      }
    } finally {
      ws.close();
    }
  }
}
```

---

## Related Notes

- MOC: [[14-Client-SDK/Client-SDK-MOC|Client-SDK-MOC]]
- Subsystem: [[01-Brain-Architecture/07-Client-Integration|07-Client-Integration]]
- SDK: [[14-Client-SDK/01-JavaScript-Client-SDK|01-JavaScript-Client-SDK]]
