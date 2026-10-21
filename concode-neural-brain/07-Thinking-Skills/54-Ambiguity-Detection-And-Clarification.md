---
title: Thinking Skill -- Ambiguity Detection And Clarification
type: thinking_skill
tags:
  - skill/ambiguity-detection
  - social/clarification
---

# Thinking Skill: Ambiguity Detection And Clarification

> Two-layer ambiguity detection system that intercepts vague or under-specified queries and returns domain-specific clarifying questions instead of generating uncertain code. Bypasses detection when conversation history provides sufficient context.

---

## Detection Layers

### Layer 1: Pattern Matching

Matches the user query against 25+ known ambiguous patterns loaded from `data/clarifying_questions.yaml`. Each pattern maps to a tailored clarifying question.

Example mappings:

| Pattern | Clarifying Question |
|---------|-------------------|
| "add authentication" | "What type of authentication -- JWT tokens, OAuth2, or session-based cookies?" |
| "make it faster" | "What's the current bottleneck -- network, computation, bundle size, or database?" |
| "fix the error" | "Could you share the error message or stack trace?" |

### Layer 2: Heuristic Rules

If no pattern matches, heuristic rules evaluate:

$$\text{Is\_Ambiguous} = (\text{word\_count} < 4 \land \text{starts\_with\_vague\_verb}) \lor (\text{word\_count} < 8 \land \text{has\_vague\_pronoun} \land \text{has\_vague\_verb})$$

**Vague verbs**: `add`, `make`, `fix`, `create`, `build`, `do`, `change`, `update`, `set up`, `improve`.

**Vague pronouns**: `it`, `this`, `that`, `the thing`, `the stuff`.

---

## Conversation History Bypass

If the session already has >= 2 conversation turns, ambiguity detection is **skipped entirely**. Follow-up queries like "now add tests for it" are valid in context.

---

## Related Notes

- MOC: [[07-Thinking-Skills/Thinking-Skills-MOC|Thinking-Skills-MOC]]
- Subsystem: [[01-Brain-Architecture/09-Social-Intelligence|09-Social-Intelligence]]
