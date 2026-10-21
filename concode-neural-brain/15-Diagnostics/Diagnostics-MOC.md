---
title: Error Diagnostics & Troubleshooting MOC
type: moc
tags:
  - diagnostics/moc
  - troubleshooting/overview
diagnostics_count: 2
---

# Error Diagnostics & Troubleshooting MOC

> Diagnostic playbooks, error recovery routines, and self-healing protocols for server administrators and developers.

---

## Diagnostics Index

| # | Error Scenario | Diagnostic Root Cause | Recovery Playbook Note |
|---|----------------|-----------------------|------------------------|
| **1** | **Model Load Failure Recovery** | Missing `.gguf` weight file in `models/` | [[15-Diagnostics/01-Model-Load-Failure-Recovery\|01-Model-Load-Failure-Recovery]] |
| **2** | **Out-Of-Memory Prevention** | KV-cache allocation exceeding Metal VRAM | [[15-Diagnostics/02-Out-Of-Memory-Prevention\|02-Out-Of-Memory-Prevention]] |

---

## Related Notes

- Back to Dashboard: [[00-Dashboard/Dashboard\|Dashboard]]
- Debugger Guild: [[02-Guilds/Debugger-Guild\|Debugger-Guild]]
