---
title: Client SDK — TripVerse AI Planner Bridge
type: sdk
tags:
  - sdk/tripverse
  - integration/travel
  - api/rest
  - client/bridge
date: 2026-10-09
---

# Client SDK: TripVerse AI Planner Bridge

> End-to-end integration protocol and schema contract connecting TripVerse travel planner interfaces with the CONCODE Neural Brain running on Kaggle GPU.

---

## 1. Overview and Architecture

The TripVerse AI Planner Bridge binds the frontend user experience of TripVerse (`AIChatDrawer`, `ConcodeBrainConfigModal`) to the hosted CONCODE neural inference engine.

```
+-------------------------------------------------------------+
|                     TripVerse Web App                       |
|   (React 19 + TypeScript + Vite + Tailwind CSS)            |
|                                                             |
|   [AIChatDrawer] <---> [concodeBrainService.ts]             |
+-------------------------------------------------------------+
                              |
                              | HTTPS (Bearer / X-API-Key)
                              v
+-------------------------------------------------------------+
|             Cloudflare Quick Tunnel / ngrok                 |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|          Kaggle GPU FastAPI Microservice (Port 8000)        |
|                                                             |
|   - /health & /ready: Telemetry and VRAM monitoring         |
|   - /api/v1/travel: Travel reasoning pipeline               |
|     * Text Mode: Co-pilot advisory                          |
|     * Itinerary Mode: Deterministic multi-day JSON          |
|     * Budget Mode: Expense distribution ledger              |
|     * Safety Mode: Risk mitigation precautions              |
+-------------------------------------------------------------+
```

---

## 2. Request Data Contracts

### TravelRequest Payload

```typescript
interface TravelRequest {
  query: string;
  trip_context: TripContext;
  session_id?: string;
  mode: "text" | "itinerary" | "budget" | "safety";
}
```

### TripContext Data Schema

```typescript
interface TripContext {
  destination: string;
  origin: string;
  duration_days: number;
  total_budget: number;
  currency: string;
  travelers_count: number;
  traveler_type: string;
  preferences: string[];
  special_requests?: string;
  transport_mode: string;
  accommodation_type: string;
  food_preference: string;
  priorities?: string[];
  known_destination_highlights?: string[];
  transport_options?: Array<Record<string, any>>;
}
```

---

## 3. Response Schema and Parsing

The endpoint `/api/v1/travel` yields a structured response tailored for immediate client-side UI rendering:

```json
{
  "ok": true,
  "reply": "Formatted markdown advice or JSON itinerary structure",
  "session_id": "concode-sess-xxxx-xxxx",
  "mode": "itinerary",
  "guild": "ai_ml",
  "is_estimate": true,
  "budget_breakdown": {
    "transport": 5600,
    "stays": 7000,
    "food": 4400,
    "activities": 2000,
    "buffer": 1000,
    "total": 20000,
    "currencySymbol": "INR"
  },
  "action_buttons": [
    { "label": "View Map Route", "action": "START_NAV" },
    { "label": "Make Cheaper", "action": "MAKE_CHEAPER" },
    { "label": "Rainy-day Alternate", "action": "RAINY_DAY_ALT" }
  ]
}
```

---

## 4. Frontend Service Implementation

The client layer in TripVerse is encapsulated within `src/services/concodeBrainService.ts`:

- **Configuration Discovery**: Reads `VITE_CONCODE_API_URL` from the environment or retrieves custom overrides from local browser storage (`tripverse_concode_config_v1`).
- **Telemetry Verification**: `checkBrainStatus()` polls the `/health` endpoint to display live GPU model availability, latency, and device status.
- **Dynamic Context Injection**: Injects live trip states, route stops, and user preferences into each query before dispatching.

---

## 5. Security and Guardrails

- **Key Authentication**: Optional `X-API-Key` and `Authorization: Bearer` token headers validate requests when a secret token is configured on the Kaggle host.
- **Budget Protection**: Models are prompted never to invent unverified live prices or ticket availability without real provider feeds.
- **Output Sanitization**: Null byte and ANSI escape sequence filters protect against downstream log injection or formatting distortion.

---

## 6. Related Notes

- Kaggle GPU Deployment: [[12-Infrastructure/04-Kaggle-GPU-Deployment|04-Kaggle-GPU-Deployment]]
- JavaScript Client SDK: [[14-Client-SDK/01-JavaScript-Client-SDK|01-JavaScript-Client-SDK]]
- Client SDK Index: [[14-Client-SDK/Client-SDK-MOC|Client-SDK-MOC]]
- Dashboard: [[00-Dashboard/Dashboard|Dashboard]]
