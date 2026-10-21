---
title: Infrastructure — Kaggle GPU Deployment
type: infrastructure
tags:
  - infra/kaggle
  - infra/gpu
  - deployment/cloud
  - integration/tripverse
date: 2026-10-09
---

# Infrastructure: Kaggle GPU Deployment

> Architecture and operational manual for hosting the CONCODE AI engine on Kaggle GPU instances (NVIDIA T4 / P100) with public tunnel ingress for TripVerse.

---

## 1. Runtime Environment Specifications

- **Compute Target**: Kaggle Notebook runtime with GPU accelerator enabled.
- **Hardware Profile**: Dual NVIDIA Tesla T4 (16 GB VRAM each) or NVIDIA Tesla P100 (16 GB VRAM).
- **Driver and Runtime**: CUDA 12.x / PyTorch 2.x with `torch.float16` precision and automatic device mapping (`device_map="auto"`).
- **Core Model Engines**:
  - Fine-tuned CONCODE GGUF / Hugging Face model loaded into GPU VRAM.
  - Native Fallback: Domain-adapted travel intelligence heuristics running in zero-latency memory.

---

## 2. Server Architecture and Endpoints

The Kaggle worker launches an asynchronous FastAPI gateway managed via `uvicorn` and `nest_asyncio` in background threads.

| Endpoint | Method | Security | Purpose |
|----------|--------|----------|---------|
| `/health` | GET | Public | Service health, device details, and GPU VRAM telemetry. |
| `/ready` | GET | Public | Model availability and backend verification. |
| `/api/v1/travel` | POST | Optional API Key | Primary TripVerse trip generation, itinerary drafting, and budget calculation. |
| `/api/v1/cognitive` | POST | Optional API Key | General code synthesis, error repair, and reasoning guild queries. |

---

## 3. Public Ingress and Tunnel Routing

Because Kaggle VM instances do not provide public static IP addresses, traffic is routed through encrypted tunnels:

1. **Cloudflare Quick Tunnel**:
   - Initialized via `pycloudflared` or direct `cloudflared` binary download.
   - Provides free, secure HTTPS endpoints without requiring account credentials.
2. **ngrok Tunnel (Secondary / Fallback)**:
   - Configured via `pyngrok` using user-supplied authentication tokens (`NGROK_AUTHTOKEN`).
3. **Local Tunnel (Tertiary)**:
   - Invoked via `npx localtunnel --port 8000`.

---

## 4. TripVerse Integration Protocol

The resulting public HTTPS URL is consumed directly by the TripVerse frontend and backend proxy services:

- **Client Configuration**: Set in TripVerse `.env` or the live UI config modal:
  - `VITE_CONCODE_API_URL="https://<tunnel-subdomain>.trycloudflare.com"`
  - `VITE_CONCODE_API_KEY="<optional-secret-token>"`
- **Payload Schema**: Strict `TravelRequest` containing `TripContext` (destination, duration, budget, travelers, food preferences, transit modes).
- **Response Schema**: Deterministic JSON payload delivering structured itinerary arrays, cost ledger distributions, and interactive action buttons.

---

## 5. Lifecycle and Operational Constraints

- **Ephemeral Sessions**: Kaggle interactive notebook sessions expire after periods of inactivity (typically 60 to 90 minutes without active interaction or up to 12 hours total execution).
- **Dynamic Hostnames**: Restarting the Kaggle session generates a new Cloudflare tunnel URL; the URL in TripVerse configuration must be refreshed accordingly.
- **Production Path**: For persistent 24/7 production hosting, transition the containerized stack defined in [[12-Infrastructure/01-Docker-Containerization|01-Docker-Containerization]] to dedicated cloud GPU instances (RunPod, Modal, or Google Cloud Vertex AI).

---

## 6. Related Notes

- TripVerse Bridge: [[14-Client-SDK/04-TripVerse-AI-Planner-Bridge|04-TripVerse-AI-Planner-Bridge]]
- Deployment Verification: [[12-Infrastructure/03-Deployment-Verification|03-Deployment-Verification]]
- Docker Containerization: [[12-Infrastructure/01-Docker-Containerization|01-Docker-Containerization]]
- Infrastructure Index: [[12-Infrastructure/Infrastructure-MOC|Infrastructure-MOC]]
- Dashboard: [[00-Dashboard/Dashboard|Dashboard]]
