---
title: Guild System & Mixture-of-Experts (MoE) Overview
type: guild_overview
tags:
  - guilds/overview
  - moe/routing
  - lora/adapters
guilds_count: 13
---

# 13 Expert Guilds & MoE Routing Overview

> Domain-specialized personas functioning as a Mixture-of-Experts (MoE) system via system prompts and fine-tuned QLoRA adapter pathways.

---

## Interactive Canvas Map

> View all guilds on Canvas: [[CONCODE-Neural-Brain-Map.canvas]]

---

## Concept & Architecture

Rather than relying on a single generic prompt, the CONCODE Neural Brain divides developer requests into 13 specialized expert guilds. Each guild has a customized system prompt, domain-specific keywords, and dedicated LoRA weight projections.

```
                    ┌────────────────────────────┐
                    │ User Natural Language Query│
                    └─────────────┬──────────────┘
                                  │
                                  ▼
                   ┌──────────────────────────────┐
                   │  Subsystem 1: Intent Class.  │
                   │ (DistilBERT / Keyword Match) │
                   └──────────────┬───────────────┘
                                  │
      ┌───────────────────────────┼───────────────────────────┐
      │                           │                           │
      ▼                           ▼                           ▼
┌───────────┐               ┌───────────┐               ┌───────────┐
│ Debugger  │               │   WebGL   │               │   AI/ML   │
└─────┬─────┘               └─────┬─────┘               └─────┬─────┘
      │                           │                           │
      └───────────────────────────┼───────────────────────────┘
                                  │
                                  ▼
                 ┌─────────────────────────────────┐
                 │  CodeLlama-7B Base + LoRA Adapters│
                 │     Guild System Prompt Injection│
                 └─────────────────────────────────┘
```

---

## Guild Summary Matrix

| Guild | Key Capabilities | Primary Keywords | Note Link |
|-------|------------------|------------------|-----------|
| **Blockchain** | Blockchain domain | `solana`, `ethereum`, `web3`, `smart-contract` | [[02-Guilds/Blockchain-Guild|Blockchain-Guild]] |
| **Debugger** | Runtime errors, stack traces, null checks | `fix`, `bug`, `TypeError`, `crash`, `undefined` | [[02-Guilds/Debugger-Guild|Debugger-Guild]] |
| **WebGL** | Three.js, shaders, particle systems, 3D | `3d`, `three.js`, `shader`, `webgl`, `glsl` | [[02-Guilds/WebGL-Guild|WebGL-Guild]] |
| **AI / ML** | PyTorch, Transformers, RAG, GGUF, Tensors | `pytorch`, `model`, `llm`, `rag`, `embedding` | [[02-Guilds/AI-ML-Guild|AI-ML-Guild]] |
| **QA** | Unit testing, Cypress, Jest, pytest, mocks | `test`, `unit test`, `jest`, `cypress`, `assert` | [[02-Guilds/QA-Guild|QA-Guild]] |
| **Security** | JWT, OAuth2, XSS/SQLi defense, OWASP | `jwt`, `security`, `auth`, `xss`, `cors`, `token` | [[02-Guilds/Security-Guild|Security-Guild]] |
| **Performance** | Latency, memory, web workers, memoization | `optimize`, `latency`, `memory`, `cache`, `throttle` | [[02-Guilds/Performance-Guild|Performance-Guild]] |
| **Database** | SQL schema, indexes, migrations, ORMs | `schema`, `sql`, `postgres`, `migration`, `index` | [[02-Guilds/Database-Guild|Database-Guild]] |
| **UI / UX** | Responsive CSS, animations | `ui`, `css`, `dark mode`, `responsive`, `tailwind` | [[02-Guilds/UI-UX-Guild|UI-UX-Guild]] |
| **DevOps** | Docker, K8s, GitHub Actions, Terraform | `docker`, `cicd`, `nginx`, `kubernetes`, `deploy` | [[02-Guilds/DevOps-Guild|DevOps-Guild]] |
| **API** | REST, GraphQL, FastAPI, OpenAPI, WebSockets | `api`, `rest`, `graphql`, `endpoint`, `fastapi` | [[02-Guilds/API-Guild|API-Guild]] |
| **Fullstack** | System architecture, monorepos (Default) | `fullstack`, `architecture`, `monorepo`, `websocket` | [[02-Guilds/Fullstack-Guild|Fullstack-Guild]] |
| **Mobile** | Mobile iOS/Android development | `mobile`, `ios`, `android`, `flutter` | [[02-Guilds/Mobile-Guild|Mobile-Guild]] |

---

## Related Notes

- Back to Dashboard: [[00-Dashboard/Dashboard|Dashboard]]
- Subsystem 1 (Intent Classifier): [[01-Brain-Architecture/01-Intent-Classifier|01-Intent-Classifier]]
- QLoRA Adapter Fine-Tuning: [[04-Experiments/QLoRA-FineTuning|QLoRA-FineTuning]]
- Reusable Guild Note Template: [[06-Templates/Guild-Template|Guild-Template]]
