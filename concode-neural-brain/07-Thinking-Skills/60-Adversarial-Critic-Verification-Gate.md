---
title: Thinking Skill -- Adversarial Critic Verification Gate
type: thinking_skill
tags:
  - skill/critic-gate
  - subsystem/swarm
---

# Thinking Skill: Adversarial Critic Verification Gate

> Audits candidate code edits and runtime outputs across Security, Performance, QA, and Completeness invariants before allowing a task to transition to `COMPLETED`.

---

## Penalty Scoring Formula

$$
S_{\text{critic}} = \max\left(0.0,\; 1.0 - \sum_{i} p_i\right)
$$

| Violation Type | Penalty $p_i$ | Auditor Guild |
|----------------|:-------------:|---------------|
| Static AST / Parser Failure | `0.35` | `qa` |
| Sandbox Unit Test Failure | `0.35` | `qa` |
| Hardcoded API Key / Secret | `0.25` | `security` |
| String-Interpolated SQL Query | `0.25` | `security` |
| Silent `except: pass` Block | `0.05` | `critic_verifier` |
| Empty Solution / No Output | `0.50` | `critic_verifier` |

A candidate passes iff $\text{issues} = \emptyset$ and $S_{\text{critic}} \ge 0.70$.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/14-Multi-Guild-Swarm|14-Multi-Guild-Swarm]]
