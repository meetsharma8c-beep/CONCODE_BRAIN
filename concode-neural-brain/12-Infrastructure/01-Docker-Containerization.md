---
title: Infrastructure — Docker Containerization
type: infrastructure
tags:
  - infra/docker
  - deployment/containers
---

# Infrastructure: Docker Containerization

> Multi-stage Docker container build definition isolating Python runtime dependencies and C++ llama-cpp-python binaries.

---

## Build Architecture

```dockerfile
FROM python:3.10-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.10-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY . .
EXPOSE 8000
CMD ["uvicorn", "src.service:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Related Notes

- MOC: [[12-Infrastructure/Infrastructure-MOC|Infrastructure-MOC]]
- Master Dashboard: [[00-Dashboard/Dashboard|Dashboard]]
