---
title: Decision Graph -- Capability-Gated Tool Bus & Critic Audit
type: decision_graph
tags:
  - decision/tools
  - decision/critic
---

# Decision Graph: Capability-Gated Tool Bus & Critic Audit

```mermaid
flowchart TD
    ToolCall["Tool Invocation Request"] --> Lookup{"Tool Registered?"}
    Lookup -->|No| ErrUnknown["Return Unknown Tool Error"]
    Lookup -->|Yes| PermCheck{"tool.permission in granted_permissions?"}
    PermCheck -->|No| ErrDenied["Reject: Capability Permission Denied"]
    PermCheck -->|Yes| URLCheck{"Is web_fetch?"}
    URLCheck -->|Yes| SSRF{"SSRF & Private IP Check Safe?"}
    SSRF -->|No| ErrSSRF["Reject Unsafe Private/Loopback Host"]
    SSRF -->|Yes| RunHandler["Execute Tool Handler"]
    URLCheck -->|No| RunHandler
    RunHandler --> CriticGate["Adversarial CriticAuditor.audit()"]
    CriticGate --> ScoreCheck{"issues == 0 and score >= 0.70?"}
    ScoreCheck -->|Yes| Approve["Approve & Commit Output"]
    ScoreCheck -->|No| Reject["Flag Issues for Self-Repair Retry"]
```

---

## Related Notes

- Decision Graphs MOC: [[08-Decision-Graphs/Decision-Graphs-MOC|Decision-Graphs-MOC]]
- Tool Bus Subsystem: [[01-Brain-Architecture/13-Universal-Tool-Bus|13-Universal-Tool-Bus]]
- Swarm Subsystem: [[01-Brain-Architecture/14-Multi-Guild-Swarm|14-Multi-Guild-Swarm]]
