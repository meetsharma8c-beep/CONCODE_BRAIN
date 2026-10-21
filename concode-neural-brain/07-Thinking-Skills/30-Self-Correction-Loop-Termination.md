---
title: Thinking Skill — Self-Correction Loop Termination
type: thinking_skill
tags:
  - skill/loop-termination
  - repair/control-flow
---

# Thinking Skill: Self-Correction Loop Termination

> Evaluates code repair iteration bounds ($N_{\text{max}} = 3$) and halts iterative self-correction loops when syntax tree checks pass.

---

## Termination Criterion

$$\text{Halt} = \text{AST\_Valid}(\hat{Y}) \quad \lor \quad (\text{iteration} \ge 3)$$

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/04-Code-Repairer|04-Code-Repairer]]
