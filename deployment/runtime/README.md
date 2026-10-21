# Persistent GPU deployment

This package runs the **existing CONCODE FastAPI service** and its local CodeLlama
GGUF through a CUDA-enabled `llama-cpp-python`. It does not use a placeholder model,
Vercel, or the optional vLLM remote backend. It contains the Docker image recipe,
a Docker Compose setup for a GPU Docker host, and manual RunPod Pod instructions.
No host or Pod is created by these files.

## Requirements and model files

- An x86-64 Linux GPU host with Docker, Docker Compose v2, NVIDIA Container Toolkit,
  and a host driver compatible with the CUDA 12.4 container.
- A CUDA GPU with **at least 16 GB VRAM recommended** for CodeLlama 7B Q4_K_M and
  the configured 4096-token context. More VRAM (24 GB+) gives additional headroom.
  GPU model/runtime memory and concurrent requests still limit capacity.
- At least 40 GB persistent disk for model artifacts, profile data, and container
  layers; more for image/build cache. The GGUF alone is about 4.08 GB.
- Model files installed separately in storage mounted at `/app/models`:
  - `codellama-7b-concode.Q4_K_M.gguf` (required for generation).
  - `intent_classifier/` and `code_repair/` with their config, weights, and tokenizer
    files (optional; the API has keyword and regex fallbacks if absent).
  - `embedder/` (optional; the current service uses the named MiniLM model and
    offline mode, so retrieval is unavailable unless its local cache is preloaded).

The weights are intentionally excluded from the Docker build context and image.
Install only model artifacts you are authorized to host under their applicable
licenses. CodeLlama uses Meta's Llama 2 Community License; check its current terms
and any applicable use restrictions before hosting or distributing it.

## RunPod Persistent GPU Pod (recommended manual target)

RunPod provisions paid compute/storage. These steps only describe configuration;
they do not create a Pod or incur charges. Choose a Secure Cloud GPU Pod whose
driver supports CUDA 12.4, with 16 GB+ VRAM, and attach a persistent Network Volume
in the same data center. Allow at least 30 GB for the container disk/image and at
least 20 GB for the Network Volume holding the model files and profile state.

1. Build the image on an x86-64 Linux Docker host and push it to a private registry.
   The CUDA `devel` image compiles the CUDA llama.cpp backend during the build:

   ```bash
   docker build --platform linux/amd64 \
     -f deployment/runtime/Dockerfile \
     -t YOUR_PRIVATE_REGISTRY/concode-brain:cuda12.4 .
   docker push YOUR_PRIVATE_REGISTRY/concode-brain:cuda12.4
   ```

   Do not build/push model files into that image. A registry credential is required
   only if the image is private; enter it through RunPod's registry-secret UI, not
   in the Dockerfile, command history, or this repository.

2. In RunPod, create a GPU Pod from that image, attach the persistent Network Volume
   at `/workspace`, set the container HTTP port to `8000`, and set these runtime
   environment variables through the Pod configuration UI. Configure port 8000 as
   an HTTP service port so RunPod can provide its HTTPS proxy:

   ```text
   CONCODE_API_KEY=<a private random value of at least 32 characters>
   CONCODE_REQUIRE_API_KEY=1
   CONCODE_INFERENCE_BACKEND=local
   CONCODE_MODEL_DIR=/workspace/models
   CONCODE_USER_PROFILES_PATH=/workspace/state/user_profiles.json
   HF_HUB_OFFLINE=1
   TRANSFORMERS_OFFLINE=1
   ```

   Generate the API key in a password manager or on a trusted machine
   (`openssl rand -hex 32`). Store it as a protected Pod environment variable. Do
   not put it in image layers, public notebook code, a browser bundle, or chat.

3. Upload the required model directories into the Network Volume so paths resolve
   exactly as `/workspace/models/codellama-7b-concode.Q4_K_M.gguf`,
   `/workspace/models/intent_classifier/`, and `/workspace/models/code_repair/`.
   The profile path's parent directory is created by the service on save.

4. Start the Pod with the image's default command. RunPod's HTTPS proxy for exposed
   port 8000 terminates TLS; use the HTTPS URL shown for the **same running Pod**.
   The Pod must remain running for the API to be reachable. A replacement Pod can
   have a different proxy URL; reserve/configure a stable custom domain and
   reverse-proxy/load-balancer separately if the service must survive Pod
   replacement without changing its address.

5. Verify readiness and then a real, authenticated inference before connecting
   any production client:

   ```bash
   export CONCODE_BASE_URL='https://<runpod-proxy-host>'
   # Set CONCODE_API_KEY in a trusted shell secret store; don't type it into a URL.
   curl --fail "$CONCODE_BASE_URL/ready"
   curl --fail "$CONCODE_BASE_URL/api/v1/status" \
     -H "X-API-Key: $CONCODE_API_KEY"
   curl --fail "$CONCODE_BASE_URL/api/v1/travel" \
     -H "X-API-Key: $CONCODE_API_KEY" \
     -H 'Content-Type: application/json' \
     -d '{"query":"Suggest a relaxed day in Kyoto","trip_context":{"destination":"Kyoto","duration_days":1},"mode":"text"}'
   ```

   `/ready` is an unauthenticated process/model-readiness probe. Travel and status
   routes require `X-API-Key`. Only configure a client with the URL after these
   requests show the real `local` backend working. Keep the key server-side and
   rotate it if it is exposed.

## Docker Compose on a GPU VM

Use this alternative when you have a persistent Linux GPU VM with inbound DNS and
ports 80/443 available. Caddy obtains and renews HTTPS certificates automatically;
port 8000 remains private on the Docker network.

```bash
cd deployment/runtime
cp .env.example .env
chmod 600 .env
# Edit .env: set a DNS name pointing to this VM and a random 32+ character API key.
# Ensure the model directory below is on persistent host storage.
CONCODE_MODEL_HOST_DIR=/srv/concode/models
./deploy.sh
```

If editing `.env` manually, include all required nonempty entries. The deployment
script rejects missing DNS/API-key/model/GPU prerequisites before building. To
update the container, run `./deploy.sh` again. To stop it, run
`docker compose down`; named profile and Caddy certificate volumes persist. Do not
pass `--volumes` unless intentionally deleting saved service data/certificates.

Set DNS A/AAAA records for the chosen domain to the VM, permit inbound TCP 80/443
(and UDP 443 for HTTP/3), and make sure the host has a persistent public address.
The `CONCODE_API_KEY` should be a random hex string, e.g. generated with
`openssl rand -hex 32`. `.env` is excluded from Docker's build context and the Git
ignore list; never commit it or paste its value into logs.

## API and runtime behavior

- `GET /health`: process is serving.
- `GET /ready`: configured text-generation model is loaded; returns 503 otherwise.
- `POST /api/v1/travel`: requires `X-API-Key`; modes are `text`, `itinerary`,
  `budget`, and `safety`.
- `POST /api/v1/cognitive`, `GET /api/v1/status`, `GET /api/v1/guilds`, and
  `POST /api/v1/agent`: protected routes also require `X-API-Key`.

One Uvicorn worker is intentional: each worker would load another copy of the
multi-billion-parameter model into GPU memory. Docker restarts the service after
process/host restart (`unless-stopped`); the health check marks the container
unhealthy until the model is loaded. Docker restart policies do not restart a
container solely because its health status is unhealthy, so use provider-level
monitoring/alerts and restart an unhealthy container after diagnosing it. A running paid GPU
Pod/VM, persistent model volume, DNS/HTTPS, valid API key, sufficient VRAM, and
successful live model inference are all required. **This bundle does not provision
that host, validate a live endpoint, or make the service always-on by itself.**
