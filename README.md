# CONCODE Neural Brain

> **Heavy-neuron cognitive engine** with **7 billion+ parameters**, 11 expert guilds,
> and 5 neural subsystems — running locally on Apple Silicon with Metal GPU acceleration.

A standalone neural brain API that replaces rule-based JavaScript engines with a
neural network–driven system. Routes user prompts to specialized expert personas,
generates code, and self-heals syntax errors.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CONCODE Neural Brain                 │
│                                                         │
│   ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│   │ DistilBERT│  │  MiniLM  │  │   CodeLlama-7B       │  │
│   │  Intent   │→│ + FAISS  │→│   (GGUF Q4_K_M)      │  │
│   │ Classifier│  │ Retriever│  │   7B params, Metal   │  │
│   └──────────┘  └──────────┘  └──────────┬───────────┘  │
│                                           │             │
│                                    ┌──────▼───────┐     │
│                                    │   CodeT5     │     │
│                                    │  Code Repair │     │
│                                    └──────────────┘     │
│                                                         │
│   Coding Agent: plan, virtual edits, verify, retry         │
│   11 Expert Guilds (prompt routing)                         │
│   [DEBUG] debugger  [WEBGL] webgl  [AI_ML] ai_ml        │
│   [QA] qa  [SEC] security  [PERF] perf  [DB] database   │
│   [UIUX] ui_ux  [DEVOPS] devops  [API] api              │
│   [FULLSTACK] fullstack (default)                       │
└─────────────────────────────────────────────────────────┘
```

### Core LLM: Billions of Neuron Connections

| Metric | Value |
|--------|-------|
| **Total Parameters** | 7,000,000,000+ (7 Billion) |
| **Transformer Layers** | 32 |
| **Attention Heads** | 32 |
| **Hidden Dimension** | 4,096 |
| **Weighted Connections** | Billions (Q/K/V/O projections + MLP layers) |
| **LoRA Rank** | 64 (alpha=128) |
| **Quantization** | Q4_K_M (GGUF) |
| **Inference** | llama.cpp + Apple Metal GPU |

### Core Subsystems

| # | Subsystem | Model | Purpose |
|---|-----------|-------|---------|
| 1 | **Intent Classifier** | DistilBERT (66M params) | Routes prompts to 11 guilds |
| 2 | **Workspace Retriever** | MiniLM + FAISS | Injects relevant code context |
| 3 | **Core LLM** | CodeLlama-7B GGUF | Guild-specialized code generation |
| 4 | **Code Repair** | CodeT5-small (60M params) | Self-heals syntax errors |
| 5 | **Session Memory** | In-memory store | Maintains conversation context |
| 6 | **Coding Agent** | Bounded orchestration loop | Plans, returns virtual file edits, verifies syntax, retries on verification failures |

---

## Project Structure

```
CONCODE_BRAIN/
├── README.md                         # This file
├── requirements.txt                  # Python dependencies
├── setup.sh                          # One-command environment setup
├── start.sh                          # Launch the server
├── .gitignore
│
├── data/
│   ├── guilds.yaml                   # 11 guild definitions + keywords
│   ├── intent_dataset.jsonl          # Intent training data (5,500 examples)
│   ├── multi_guild_train.jsonl       # LLM fine-tuning data (5,500 examples)
│   └── repair_dataset.jsonl          # Code repair pairs (10,000 pairs)
│
├── src/
│   ├── __init__.py
│   ├── config.py                     # Centralized configuration
│   ├── service.py                    # FastAPI cognitive engine
│   ├── generate_data.py              # Training data generator
│   ├── convert_to_gguf.sh            # HF model → GGUF conversion
│   ├── train_colab.ipynb             # Google Colab training notebook
│   └── brain/
│       ├── __init__.py
│       ├── intent.py                 # Intent classifier (DistilBERT)
│       ├── retriever.py              # Workspace retriever (MiniLM + FAISS)
│       ├── generator.py              # Code generator (CodeLlama GGUF)
│       └── repair.py                 # Code repair (CodeT5)
│
├── integration/
│   └── concode_brain_client.js       # Website integration snippet
│
└── models/                           # Trained model weights (git-ignored)
    ├── codellama-7b-concode.Q4_K_M.gguf
    ├── intent_classifier/
    ├── code_repair/
    └── embedder/
```

---

## Quick Start

### Prerequisites

- **macOS** with Apple Silicon (M1/M2/M3/M4)
- **Python 3.10+**
- **Xcode Command Line Tools**: `xcode-select --install`
- **Google account** for Colab (training only)

### Step 1: Setup Environment

```bash
cd CONCODE_BRAIN
chmod +x setup.sh start.sh src/convert_to_gguf.sh
./setup.sh
```

This creates a virtual environment, installs all dependencies (including
`llama-cpp-python` with Metal), downloads the MiniLM embedder, and generates
training data.

### Step 2: Generate Training Data

```bash
source venv/bin/activate
python -m src.generate_data
```

This creates 3 files in `data/`:
- `intent_dataset.jsonl` — 5,500 intent examples
- `repair_dataset.jsonl` — 10,000 broken/fixed code pairs
- `multi_guild_train.jsonl` — 5,500 guild training examples

### Step 3: Train Models on Google Colab

1. Open [Google Colab](https://colab.research.google.com)
2. Upload `src/train_colab.ipynb`
3. Set runtime to **GPU → T4**
4. Run all cells in order
5. Upload the 3 data files when prompted
6. Download the trained model archives when complete

Training takes ~45-60 minutes on a free T4 GPU.

### Step 4: Install Trained Models

After downloading from Colab:

```bash
# Unzip to the models directory
unzip intent_classifier.zip -d models/intent_classifier/
unzip code_repair.zip -d models/code_repair/
unzip codellama-7b-concode-merged.zip -d models/codellama-7b-concode-merged/
```

### Step 5: Convert LLM to GGUF

```bash
bash src/convert_to_gguf.sh
```

This clones llama.cpp, builds with Metal, converts to F16, then quantizes to Q4_K_M.
The resulting file is ~4GB at `models/codellama-7b-concode.Q4_K_M.gguf`.

### Distribute the Local Model to Another Project

Keep the 3.8 GB GGUF outside Git and publish it only through a location that is
authorized for the underlying model license, such as a private release asset or
private object storage. Generate its checksum from this workspace:

```bash
./scripts/model_checksum.sh
```

In another checkout, install the exact artifact with checksum verification:

```bash
./scripts/download_model.sh \
  --url "https://your-authorized-host.example/releases/codellama-7b-concode.Q4_K_M.gguf" \
  --sha256 "PASTE_THE_64_CHARACTER_SHA256_HERE"
```

The installer accepts the same values through `CONCODE_MODEL_URL` and
`CONCODE_MODEL_SHA256`. It downloads only the GGUF file, verifies it before it
is installed, and keeps a mismatched existing model unless `--force` is given.
Inference remains entirely local after installation; the API never calls an
external AI provider.

### Optional Remote Self-Hosted GPU Inference

For a persistent GPU host running the actual FastAPI brain, see
[`deployment/runtime/README.md`](deployment/runtime/README.md). It documents a
RunPod Persistent GPU Pod path and a Docker Compose + Caddy path for a GPU VM;
neither path provisions resources automatically.

CONCODE defaults to the bundled local model on this device. For heavier workloads,
you can set `CONCODE_INFERENCE_BACKEND=remote` and use a GPU server you control.
It uses the OpenAI-compatible HTTP format only as a protocol; it does not call
OpenAI or any other hosted AI provider. vLLM provides an official container for
this kind of server and supports an API key. Keep the vLLM service on a private
network or behind a TLS reverse proxy: its own API key does not protect every
endpoint.
[vLLM Docker documentation](https://docs.vllm.ai/en/stable/deployment/docker/)
and [server security note](https://docs.vllm.ai/en/v0.30.0/serving/online_serving/openai_compatible_server/) explain these deployment details.

### Lightweight TripVerse API on Hugging Face

For a free-tier prototype without uploading the 4 GB local model, use the
[`deployment/huggingface/` Docker Space](deployment/huggingface/README.md). It
hosts a small, authenticated ConCode travel API on Hugging Face Spaces and sends
generation to an OpenAI-compatible inference provider selected through Space
Secrets. Hugging Face Inference Providers or an eligible NVIDIA hosted-inference
credit account can be used as the primary/fallback private provider; TripVerse
still calls only ConCode's `/api/v1/travel` endpoint and never receives a
provider credential.

This is a travel-only ConCode API adapter, not the full coding brain or its local
CodeLlama model. Free Spaces can sleep and provider credits are quota-limited, so
expect cold starts and verify real itinerary inference before configuring the
TripVerse Vercel server-side `CONCODE_API_URL` and `CONCODE_API_KEY` values.

On the GPU server:

```bash
cd deployment/vllm
cp .env.example .env
# Edit .env: set an authorized coding model and long random API key.
docker compose up -d
```

Expose it only through your own HTTPS endpoint, for example
`https://llm.example.com/v1`. Then configure CONCODE by copying
`.env.example` to `.env` and setting the remote endpoint, model name
(`concode-coder` for the included vLLM configuration), and its API key.

### Step 6: Start the Server

```bash
./start.sh
```

The server starts at `http://localhost:8000`.

> **Note**: Local inference is the default. If the selected local or remote model
> is unavailable or fails, the API returns an error rather than a canned response
> or a request to another provider.

### Colab GPU API Prototype

For an initial callable API when the local Mac is unavailable, open
[`deployment/colab/CONCODE_BRAIN_Colab_API.ipynb`](deployment/colab/CONCODE_BRAIN_Colab_API.ipynb)
in Google Colab and select a CUDA GPU runtime. Copy the project source and trained
model directories to `MyDrive/CONCODE_BRAIN`; the GGUF, intent, and repair weights
total about 4.3 GB. Add `CONCODE_API_KEY` (at least 32 random characters) and
`NGROK_AUTHTOKEN` as Colab Secrets and enable access for the notebook. The notebook
builds CUDA-enabled llama.cpp, starts this FastAPI service with its existing local
GGUF backend, verifies the loaded model and a real inference request, then opens
an HTTPS ngrok tunnel. It never writes either secret into the notebook or prints
them.

The notebook exposes the existing `/api/v1/cognitive`, `/api/v1/status`,
`/api/v1/guilds`, and `/health` routes; protected routes require `X-API-Key`.
Colab may sleep or reclaim its runtime, and tunnel URLs change after restarts, so
this is an ephemeral prototype, not a stable production deployment. Do not point
production clients at it until the notebook has passed its real inference check
and the live endpoint has been independently verified.

### Kaggle GPU API Prototype

Kaggle can be used as another temporary GPU runtime. See
[`deployment/kaggle/CONCODE_BRAIN_Kaggle_GPU_API.ipynb`](deployment/kaggle/CONCODE_BRAIN_Kaggle_GPU_API.ipynb)
for a notebook that loads the actual local model from an attached private Kaggle
Dataset, reads `CONCODE_API_KEY` from Kaggle Secrets, tests the authenticated
`/api/v1/travel` itinerary route, and only then opens a temporary HTTPS
Cloudflare quick tunnel. Upload
`deployment/kaggle/concode_kaggle_dataset.zip` as a **private** Dataset input;
the archive contains only the necessary source, YAML configuration, and model
files, excluding `.env`, virtual environments, and profiles. Kaggle requires
the notebook's GPU and Internet settings to be enabled; availability and free
GPU quotas vary by account and may change. The session and tunnel can stop at
any time, so this is a prototype, not an always-on endpoint. The notebook
doesn't need a Kaggle API token; use the browser UI and Kaggle Secrets instead.

### Using CONCODE From Your Apps

An app running on this same device can call `http://localhost:8000` directly.
For other users, do not expose the Mac's port 8000 directly to the public
internet. Keep the server online and use a TLS-protected reverse proxy or a
private network/VPN, set `CONCODE_API_KEY` to a long random value, and set
`CONCODE_CORS_ORIGINS` to the exact HTTPS origins of your apps. A local 7B model
also has limited concurrent capacity, so it is best for personal use, prototypes,
or a small number of users; use the optional remote GPU setup as demand grows.

---

## API Reference

### `POST /api/v1/cognitive`

The main endpoint. Runs the full neural pipeline.

**Request:**
```json
{
  "query": "Fix the null pointer error in my login handler",
  "workspace_files": {
    "auth.js": "function login(user) { return user.name; }",
    "index.js": "const app = express();"
  },
  "session_id": "abc-123",
  "mode": "text"
}
```

**Response:**
```json
{
  "code": "function login(user) {\n  if (!user) return null;\n  return user.name;\n}",
  "guild": "debugger",
  "guild_icon": "🩺",
  "confidence": 0.95,
  "repair_applied": false,
  "session_id": "abc-123",
  "subsystems": {
    "intent": "neural",
    "retriever": "indexed_2_files",
    "generator": "gguf_metal",
    "repair": "neural"
  },
  "latency_ms": 1250.5
}
```

### Agent Endpoint

`POST /api/v1/agent` runs a bounded coding-agent loop on a project snapshot.
It plans a change, returns complete replacement files, validates supported syntax,
and retries up to three times when validation fails. It never reads or writes the
server filesystem and never executes submitted project code. It requires the
configured model on your own remote GPU server; it does not call a public AI
provider or return a canned template when that model is unavailable. The calling
project reviews and applies the returned diffs.

```json
{
  "goal": "Add a health endpoint and return JSON",
  "workspace_files": {
    "app.py": "from fastapi import FastAPI\napp = FastAPI()\n"
  },
  "max_iterations": 3
}
```

The response includes `plan`, complete-file `edits`, unified `diff` text, and
per-file `verification` results. Python, JSON, YAML, JavaScript, and basic
delimiter checks for TypeScript, JSX, CSS are supported. A successful response
means the proposed change passed those checks; it does not guarantee behavior or
test-suite correctness.

The browser client exposes the same workflow without applying any change by
default. The integrating project must explicitly decide how to save the returned
whole-file edits:

```js
const result = await ConcodeBrain.agent('Add a health endpoint', {
  workspaceFiles: projectSnapshot,
  onEdits: async (edits) => reviewAndApply(edits),
});
```

### Other Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Server status |
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/guilds` | List all guilds |
| `GET` | `/api/v1/status` | Detailed subsystem status |
| `POST` | `/api/v1/agent` | Plan, edit, and verify a supplied workspace snapshot |

---

## 🌐 Website Integration

Add this to your Antigravity-built website:

```html
<script src="concode_brain_client.js"></script>
<script>
  // Check if brain is online
  ConcodeBrain.isOnline().then(online => {
    console.log('Brain status:', online ? '🟢 Online' : '🔴 Offline');
  });

  // Query the brain
  async function askBrain(prompt) {
    const result = await ConcodeBrain.query(prompt);
    console.log(`${result.guild_icon} ${result.guild}: ${result.code}`);
  }

  // Query and insert code directly into the editor
  async function generateCode(prompt) {
    await ConcodeBrain.queryAndInsert(prompt);
  }
</script>
```

---

## 🔧 Configuration

All settings are in `src/config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `LLM_GPU_LAYERS` | 99 | Layers offloaded to Metal GPU |
| `LLM_CONTEXT_LENGTH` | 4096 | Context window size |
| `LLM_MAX_TOKENS` | 2048 | Max generation tokens |
| `LLM_TEMPERATURE` | 0.3 | Generation temperature |
| `RETRIEVER_TOP_K` | 3 | Number of context chunks |
| `SESSION_MAX_HISTORY` | 3 | Turns kept per session |

---

## 📋 Training Details

### QLoRA Configuration

| Parameter | Value |
|-----------|-------|
| Base Model | `codellama-7b-instruct-bnb-4bit` |
| Quantization | 4-bit (bitsandbytes) |
| LoRA Rank (r) | 64 |
| LoRA Alpha | 128 |
| Target Modules | q, k, v, o, gate, up, down projections |
| Learning Rate | 2e-4 |
| Batch Size | 2 (×4 gradient accumulation) |
| Max Steps | 300 |
| Optimizer | AdamW 8-bit |

### Intent Classifier

| Parameter | Value |
|-----------|-------|
| Base Model | `distilbert-base-uncased` |
| Classes | 11 guilds |
| Epochs | 5 |
| Batch Size | 16 |
| Learning Rate | 5e-5 |

### Code Repair

| Parameter | Value |
|-----------|-------|
| Base Model | `Salesforce/codet5-small` |
| Task | Seq2Seq (broken → fixed) |
| Epochs | 5 |
| Batch Size | 8 |
| Learning Rate | 5e-5 |

---

## 🛠️ Troubleshooting

### Server won't start
```bash
# Ensure venv is active
source venv/bin/activate

# Check dependencies
pip install -r requirements.txt

# Run directly
uvicorn src.service:app --host 0.0.0.0 --port 8000
```

### Metal GPU not working
```bash
# Reinstall llama-cpp-python with Metal
pip uninstall llama-cpp-python -y
CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python --no-cache-dir
```

### GGUF conversion fails
```bash
# Make sure you have Xcode CLT
xcode-select --install

# Rebuild llama.cpp
cd llama.cpp
make clean && make GGML_METAL=1 -j$(sysctl -n hw.ncpu)
```

### Colab runs out of memory
- Reduce `max_steps` from 300 to 150
- Reduce `LoRA r` from 64 to 32
- Use `packing=True` in SFTTrainer

---

## 📜 License

All tools used are free and open-source:
- **CodeLlama**: Meta AI (Llama 2 Community License)
- **DistilBERT**: HuggingFace (Apache 2.0)
- **CodeT5**: Salesforce (BSD 3-Clause)
- **MiniLM**: Microsoft (MIT)
- **llama.cpp**: MIT
- **FAISS**: Meta AI (MIT)
- **FastAPI**: MIT
