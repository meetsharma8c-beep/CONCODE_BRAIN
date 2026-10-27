---
title: ConCode Trip Planner API
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
---

# ConCode Trip Planner API on Hugging Face Spaces

This lightweight Docker Space exposes ConCode's authenticated
`POST /api/v1/travel` contract for TripVerse. It keeps ConCode's travel planning
instructions, response validation, and `X-API-Key` protection, while sending
generation to a configured OpenAI-compatible hosted model API. It does **not**
host or reproduce ConCode's local CodeLlama weights or the full coding-agent
brain. The Space uses CPU for the small API process; the configured inference
provider runs the actual model.

## Create and configure the Space

1. Create a new Hugging Face Space, select **Docker**, and choose the free CPU
   hardware to start. Copy the files in this directory to the Space repository
   root (`README.md`, `Dockerfile`, `app.py`, and `requirements.txt`).
2. In Space **Settings → Variables and secrets**, add:

   - Secret `CONCODE_API_KEY`: private random value, at least 32 characters.
   - Secret `CONCODE_REMOTE_LLM_API_KEY`: the API-provider token.
   - Variable `CONCODE_REMOTE_LLM_BASE_URL`: HTTPS OpenAI-compatible API base,
     ending in `/v1`.
   - Variable `CONCODE_REMOTE_LLM_MODEL`: model identifier supported by the
     selected provider.
   - Optional variable `CONCODE_REMOTE_LLM_TIMEOUT_SECONDS`: defaults to `6`.

3. Configure Hugging Face Inference Providers as the primary inference provider:

   **Hugging Face Inference Providers** (if the account/model has available
   credits and provider support):

   ```text
   CONCODE_REMOTE_LLM_BASE_URL=https://router.huggingface.co/v1
   CONCODE_REMOTE_LLM_MODEL=<a chat model currently available to your account>
   CONCODE_REMOTE_LLM_API_KEY=<HF token with inference permission>
   ```

4. Optionally configure NVIDIA NIM as a fallback provider using these additional
   Space settings:

   ```text
   CONCODE_FALLBACK_LLM_BASE_URL=https://integrate.api.nvidia.com/v1
   CONCODE_FALLBACK_LLM_MODEL=meta/llama-3.1-8b-instruct
   CONCODE_FALLBACK_LLM_API_KEY=<NVIDIA API key>
   ```

   ConCode tries the primary provider first and tries the NVIDIA fallback only
   when primary inference fails or returns invalid itinerary output. If using
   NVIDIA only, put its URL/model/key in the primary `CONCODE_REMOTE_LLM_*`
   settings and leave the fallback settings empty. Keep every token in Space
   Secrets, never in the Space README, image, browser, TripVerse repository, or
   public logs. Provider free credits, trial quotas, model availability, and
   rate limits are controlled by each provider and may change. Hosted provider
   models are not ConCode's local CodeLlama model; ConCode's API layer supplies
   the travel-planning behavior and validates results.

5. Wait for the Space to become **Running**. Its API base URL is
   `https://<account>-<space-name>.hf.space`.
5. Verify without exposing secrets:

   ```bash
   export CONCODE_BASE_URL='https://<account>-<space-name>.hf.space'
   curl --fail "$CONCODE_BASE_URL/ready"
   curl --fail "$CONCODE_BASE_URL/api/v1/travel" \
     -H "X-API-Key: $CONCODE_API_KEY" \
     -H 'Content-Type: application/json' \
     -d '{"query":"Create a one-day itinerary for Goa","trip_context":{"destination":"Goa","duration_days":1,"travelers_count":2,"currency":"INR"},"mode":"itinerary"}'
   ```

   `/ready` checks configuration only. The authenticated itinerary request is
   required to verify real inference and structured output.

## Connect TripVerse

Only after the authenticated inference request succeeds, add these **Production**
environment variables to the TripVerse Vercel project:

- `CONCODE_API_URL=https://<account>-<space-name>.hf.space`
- `CONCODE_API_KEY=<the same private ConCode API key configured in Space Secrets>`

TripVerse sends requests only to this ConCode endpoint and sends the key only in
the server-side `X-API-Key` header. Provider API credentials remain exclusively
in Space Secrets. Redeploy TripVerse after setting the Vercel variables.

## Free-host limitations

Hugging Face free CPU Spaces can sleep when idle, and hosted inference credits
are quota-limited. Cold starts can exceed the TripVerse proxy timeout; the app
will then clearly fall back to its local preview. This setup is a low-cost
prototype, not an always-on or latency-guaranteed production service. Monitor
provider quotas and Space sleep behavior before advertising live AI availability.
