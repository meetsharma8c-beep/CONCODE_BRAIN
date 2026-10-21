---
title: Infrastructure & Deployment MOC
type: moc
tags:
  - infra/moc
  - deployment/overview
infra_count: 4
---

# Infrastructure & Deployment MOC

> Containerization, process orchestration, and Metal GPU acceleration setups powering the CONCODE Neural Brain server.

---

## Infrastructure Index

| # | Component | Primary Technology | Note Link |
|---|-----------|-------------------|-----------|
| **1** | **Docker Containerization** | Multi-stage Dockerfile & compose setup | [[12-Infrastructure/01-Docker-Containerization|01-Docker-Containerization]] |
| **2** | **Apple Silicon Metal Setup** | Metal Performance Shaders (MPS) compilation | [[12-Infrastructure/02-Apple-Silicon-Metal-Setup|02-Apple-Silicon-Metal-Setup]] |
| **3** | **Deployment Verification** | Finalized training, quantization, and service rollout | [[12-Infrastructure/03-Deployment-Verification|03-Deployment-Verification]] |
| **4** | **Kaggle GPU Deployment** | Cloud GPU hosting with Cloudflare tunnel ingress | [[12-Infrastructure/04-Kaggle-GPU-Deployment|04-Kaggle-GPU-Deployment]] |

---

## Related Notes

- Back to Dashboard: [[00-Dashboard/Dashboard\|Dashboard]]
- DevOps Guild: [[02-Guilds/DevOps-Guild\|DevOps-Guild]]
