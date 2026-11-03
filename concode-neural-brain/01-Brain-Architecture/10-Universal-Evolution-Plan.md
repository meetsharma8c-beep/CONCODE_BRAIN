---
title: Universal Cognitive Evolution Master Plan
type: architecture
tags:
  - system/brain
  - architecture/evolution
  - status/planned
version: 3.0.0
---

# Universal Cognitive Evolution Master Plan

> Architectural blueprint for evolving the CONCODE Neural Brain from a bounded 7B single-domain coding engine into an autonomous, tool-augmented, multi-guild universal problem-solving system.

---

## 1. Current Bottleneck Diagnosis

The existing cognitive architecture in [[01-Brain-Architecture/00-Brain-Overview|00-Brain-Overview]] is constrained by six structural limits:

| Bottleneck | Current Implementation | Universal Requirement |
| :--- | :--- | :--- |
| **Action Isolation** | `CodingAgent` operates purely on in-memory file snapshots without execution or external I/O. | Sandboxed execution runtime, shell/process control, web & API tool protocol (MCP). |
| **Single-Guild Routing** | `IntentClassifier` picks a single Guild per prompt (`top-1` classification). | Hierarchical DAG planner that decomposes complex goals across multiple Guilds simultaneously. |
| **Shallow Reasoning Loop** | Maximum 3 linear retry iterations checking only static syntax (`ast.parse`). | Tree-of-Thoughts (ToT) + MCTS reasoning with semantic test execution and critic verification. |
| **Ephemeral Memory** | `session_store` holds 3 turns in RAM; FAISS re-indexes from scratch per request. | Persistent episodic vector memory, cross-session knowledge graph, and automatic Obsidian vault synthesis. |
| **Fixed 7B Horizon** | Single local `CodeLlama-7B` (`4096` context window) handles all tasks. | Hybrid compute router combining fast local GGUF models with frontier reasoning models and long-context windows. |
| **Static Weights** | Training requires manual dataset generation and external Colab notebooks. | Self-evolving continual learning loop that harvests verified trajectories into LoRA fine-tuning datasets. |

---

## 2. Target Universal Architecture (CONCODE v3.0)

```mermaid
flowchart TD
    Input["Universal Goal / Multimodal Input"] --> Cortex["Executive Meta-Planner (DAG Decomposition)"]
    
    Cortex --> Router["Multi-Guild Swarm Orchestrator"]
    
    subgraph Compute["Hybrid Neural Compute Layer"]
        LocalLLM["Local Metal Engine (7B-32B GGUF)"]
        FrontierLLM["Remote / Frontier Reasoning Engine"]
        Classifier["DistilBERT Intent & Sentiment Routers"]
    end
    
    Router <--> Compute
    
    subgraph Action["Universal Tool & Execution Bus"]
        Sandbox["Sandboxed Code & Shell Runner"]
        WebResearch["Web Search, Browser & API Client"]
        FSManager["Workspace & Git Transaction Manager"]
        MCPBridge["Universal MCP Tool Protocol"]
    end
    
    Router --> Action
    
    subgraph Verification["Closed-Loop Critic & Verification"]
        SyntaxCheck["Static AST & Type Verifier"]
        RuntimeTest["Automated Test & Execution Verifier"]
        SelfHeal["CodeT5 + Critic Self-Repair Loop"]
    end
    
    Action --> Verification
    Verification -->|Pass| Memory["Continual Memory & Vault Synthesizer"]
    Verification -->|Fail: Backtrack| Cortex
    
    subgraph Knowledge["Persistent Cognitive Memory"]
        VectorDB["Persistent FAISS / Episodic Store"]
        ObsidianVault["Obsidian Knowledge Graph & Canvas"]
        LoRA Harvesters["Automated DPO / QLoRA Dataset Harvester"]
    end
    
    Memory --> Knowledge
```

---

## 3. Six-Pillar Engineering Roadmap

### Pillar I: Executive Meta-Planner & System-2 Reasoning (`src/brain/planner.py`)
Transform the brain from single-shot generation into a deliberate reasoning engine:
- **Hierarchical Goal Decomposition**: Break arbitrary real-world objectives into a Directed Acyclic Graph (DAG) of verifiable sub-tasks (`PlanNode`, `DependencyEdge`).
- **Hypothesis-Test-Reflect Loop**: Before committing to an output, generate multiple candidate strategies, score them with an internal Critic rubric, and backtrack automatically when a path fails.
- **Explicit Scratchpad & State Machine**: Persist intermediate reasoning states (`PENDING`, `EXECUTING`, `VERIFYING`, `BACKTRACKING`, `COMPLETED`) so long-horizon tasks survive across turns.

### Pillar II: Universal Tool Bus & Sandboxed Execution (`src/brain/tools.py` & `src/brain/sandbox.py`)
Give the brain hands to interact with the real world safely:
- **Sandboxed Runtime Executor**: Execute Python, Node.js, Rust, and shell workflows inside isolated subprocess/container sandboxes with strict CPU, memory, and timeout quotas—replacing static syntax-only checks with real runtime verification.
- **Model Context Protocol (MCP) Bridge**: Native client support for MCP servers so the brain can dynamically discover and invoke external tools (databases, web browsers, cloud APIs, scientific instruments, file systems).
- **Autonomous Web & Literature Research**: Integrate live documentation fetching, search engines, and API probing so the brain can learn unfamiliar libraries or real-world facts on the fly.
- **Capability-Gated Safety Layer**: Tiered permission policy (`READ_ONLY`, `SANDBOX_WRITE`, `EXTERNAL_NETWORK`, `HUMAN_APPROVAL_REQUIRED`) integrated into `src/brain/security.py`.

### Pillar III: Multi-Guild Swarm Orchestration (`src/brain/swarm.py`)
Upgrade from 13 isolated personas to a collaborative expert network:
- **Multi-Label Guild Activation**: Allow `IntentClassifier` to activate an ensemble of Guilds (e.g., `architect` + `database` + `security` + `qa`) for a single complex problem.
- **Adversarial Red-Team / Blue-Team Review**: Every solution proposed by a Builder Guild (`fullstack`, `api`, `ai_ml`) is automatically audited by `security`, `performance`, and `qa` Guilds before completion.
- **New Universal Guilds**: Expand `data/guilds.yaml` beyond coding to include:
  - `system_architect` (first-principles decomposition & distributed systems)
  - `research_scientist` (mathematical modeling, literature synthesis, data analysis)
  - `automation_operator` (OS automation, APIs, workflows, scraping)
  - `critic_verifier` (formal verification, edge-case falsification)

### Pillar IV: Persistent Episodic, Semantic & Graph Memory (`src/brain/memory.py`)
Eliminate amnesia across requests and sessions:
- **Persistent Vector Index**: Upgrade `WorkspaceRetriever` from ephemeral per-request indexing to a persistent, incremental disk-backed FAISS + SQLite metadata index with AST-aware symbol chunking.
- **Episodic Experience Store**: Record every solved problem, failed attempt, and root-cause fix into a long-term episodic store (`data/episodic_memory.jsonl`). When a similar problem appears in the future, retrieve past winning trajectories (Few-Shot Experience Replay).
- **Bidirectional Obsidian Vault Coupling**: Connect `src/obsidian_auto_mapper.py` and `src/canvas_graph_builder.py` directly into the runtime loop so the brain reads and writes structured notes in `concode-neural-brain/` as its live semantic knowledge graph.

### Pillar V: Hybrid Neural Compute & Dynamic Model Scaling (`src/brain/router.py`)
Remove the ceiling of a single 7B 4K-context model:
- **Complexity-Aware Compute Router**: Score incoming sub-tasks by difficulty and context size:
  - **Tier 1 (Fast Reflex)**: DistilBERT + CodeT5 + local 7B GGUF for sub-second routing, syntax repair, and boilerplate generation.
  - **Tier 2 (Deep Local Reasoning)**: Support multi-model local GGUF switching (`DeepSeek-R1-Distill`, `Qwen2.5-Coder-14B/32B`, `Llama-3.3`) with `32k-128k` context windows on Apple Metal.
  - **Tier 3 (Frontier Escalation)**: Seamless fallback via `RemoteCodeGenerator` to high-capacity cloud/frontier endpoints when a task exceeds local hardware memory or fails local verification twice.

### Pillar VI: Self-Evolving Continual Learning Loop (`src/brain/evolution.py`)
Make the brain smarter every day from its own work:
- **Trajectory Harvesting**: Whenever a task passes all verification checks (or gets corrected during human feedback), log the `(prompt, reasoning_trace, winning_solution, rejected_attempts)` tuple.
- **Automated Dataset Synthesis**: Periodically compile harvested trajectories into `data/multi_guild_train.jsonl` and Direct Preference Optimization (DPO) pairs.
- **Local MLX / QLoRA Nightly Adapter Updates**: Use Apple Silicon MLX / PyTorch MPS (`src/train_models_local.py`) to fine-tune lightweight guild LoRA adapters locally without needing external GPUs.

---

## 4. Phased Implementation Sequence

| Phase | Target Modules | Core Deliverable |
| :--- | :--- | :--- |
| **Phase 1: Executive Planner & Deep Agent Loop** | `src/brain/planner.py`, `src/brain/agent.py` | DAG task decomposition, multi-step reflection, and unrestricted iteration depth with state persistence. |
| **Phase 2: Universal Tool Bus & Sandbox** | `src/brain/tools.py`, `src/brain/sandbox.py`, `src/service.py` | Safe code/test execution, filesystem transactions, web research tools, and MCP tool protocol. |
| **Phase 3: Multi-Guild Swarm & Critic** | `src/brain/swarm.py`, `src/brain/intent.py`, `data/guilds.yaml` | Multi-guild collaboration, universal non-coding guilds, and automated `security`/`qa` verification gates. |
| **Phase 4: Persistent Memory & Vault Sync** | `src/brain/memory.py`, `src/brain/retriever.py`, `src/obsidian_auto_mapper.py` | Incremental persistent FAISS index, episodic experience replay, and live Obsidian knowledge synthesis. |
| **Phase 5: Hybrid Compute & Self-Evolution** | `src/brain/router.py`, `src/brain/evolution.py`, `src/config.py` | Multi-model Tier 1/2/3 compute routing, 32k+ context window support, and automated LoRA trajectory harvesting. |

---

## Related Vault Nodes
- [[00-Dashboard/Dashboard|Master Dashboard]]
- [[01-Brain-Architecture/00-Brain-Overview|00-Brain-Overview]]
- [[01-Brain-Architecture/08-Neural-Thinking-Process|08-Neural-Thinking-Process]]
- [[08-Decision-Graphs/Decision-Graphs-MOC|Decision-Graphs-MOC]]
- [[CONCODE-Neural-Brain-Map.canvas]]
