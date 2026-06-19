---
document_type: service
summary: >-
  The backend is a Python FastAPI server (port 8000) that acts as the sole API
  layer for the FanFest platform. It is responsible for serving the REST API
  consu...
last_updated: '2026-06-19T18:45:00.000Z'
tags:
  - service
  - python
  - backend
  - fastapi
service_id: backend
---
# Fan Fest Backend

## Purpose

The backend is a Python FastAPI server (port 8000) that acts as the sole API layer for the FanFest platform. It is responsible for serving the REST API consumed by the [[frontend]], proxying all calls to external third-party services (Anthropic, Google), and owning the AI-generated event recap feature. The backend is operational at the infra baseline: `app/main.py` has a working FastAPI application and `requirements.txt` declares pinned runtime dependencies.

## Public API / Surface

| Method | Path | Response | Notes |
|--------|------|----------|-------|
| `GET` | `/health` | `{"status": "ok"}` (HTTP 200) | Infrastructure health probe; no auth required |
| `GET` | `/api/v1/events/{event_id}` | `EventDetail` (HTTP 200) | Full event detail: teams, venue, time, organizer, attendees, invite/calendar/maps links |
| `POST` | `/api/v1/events/{event_id}/predictions` | `PredictionResponse` (HTTP 200) | Submit or overwrite a per-user scoreline prediction; locked (HTTP 409) after mocked match-start time |
| `POST` | `/api/v1/events/{event_id}/checkin` | `CheckinResponse` (HTTP 200) | Mark user present; idempotent. HTTP 400 if no user identity supplied |

The intended pattern for product routes places handlers under `fanfest/backend/app/api/v1/endpoints/{domain}.py`, each domain in its own module, routers registered in `fanfest/backend/app/main.py` via `app.include_router(router)`. The `/health` endpoint is an infra-only exception defined inline in `main.py`. FastAPI auto-generates OpenAPI docs at `/docs` and `/redoc` once the server is running.

## Internal Architecture

The directory tree follows a standard FastAPI layered layout:

```
fanfest/backend/
├── app/
│   ├── main.py               # FastAPI app entry; router registration
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/    # one module per domain
│   ├── core/                 # config, settings modules
│   ├── models/               # (planned) ORM or data models
│   ├── schemas/              # Pydantic request/response models
│   └── services/             # (planned) business logic
└── tests/                    # pytest test suite
```

`app/main.py` contains the live FastAPI app. `api/v1/endpoints/events.py` is the first product-domain endpoint module; `schemas/events.py` holds its Pydantic models; `services/events_service.py` holds business logic and the in-process store. `tests/test_health.py` and `tests/test_events.py` are the implemented test files. `core/` and `models/` remain empty stubs. No ORM, auth library, or database client has been declared.

## Request Lifecycle

1. HTTP request arrives at uvicorn on port 8000
2. FastAPI routes to the matching handler (`GET /health` is inline in `main.py`; product routes will live in `api/v1/endpoints/{domain}.py`)
3. Handler calls into `services/` for business logic (product routes only)
4. Service calls external APIs (Anthropic, Google) using credentials from env vars
5. Response serialized via Pydantic schema and returned

CORS middleware is configured in `main.py` allowing `http://localhost:8080` (the [[frontend]] origin) because there is no reverse proxy in local development. `allow_credentials=True` is set with the explicit single origin.

## Data Layer

An in-process dict store introduced by FEST-02 provides lightweight persistence for the lifetime of the running process. Three module-level dicts in `app/services/events_service.py`:

| Store | Key | Value |
|-------|-----|-------|
| `_events` | `event_id: str` | event detail dict (seeded with mock event `evt-001`) |
| `_predictions` | `(user_id, event_id): tuple` | prediction dict `{user_id, event_id, home_score, away_score}` |
| `_attendees` | `event_id: str` | `set[str]` of checked-in user IDs |

No external database, ORM, cache, or object store. State resets on server restart. No DB client in `requirements.txt`.

## Configuration

| Variable | Behavior |
|----------|----------|
| `ANTHROPIC_API_KEY` | Gates the AI recap feature; without it, Anthropic API calls will fail |
| Google OAuth credentials | Gates Calendar, Maps, and Drive integrations; see `fanfest/backend/.env.example` for exact variable names |

Copy `.env.example` to `.env` and populate before starting the server:

```bash
cd fanfest/backend
cp .env.example .env
```

## Integrations

All external integrations are backend-side. The [[frontend]] does not call any external APIs directly.

| External Service | Type | Role |
|------------------|------|------|
| Anthropic API | AI/LLM | AI-generated post-event recap (hero feature) |
| Google Calendar API | Google Cloud | Calendar integration |
| Google Maps API | Google Cloud | Location/maps integration |
| Google Drive API | Google Cloud | Document/file integration |

The Anthropic integration generates a personalized narrative recap given event context (location, date, attendance, match highlights). Claude was chosen because it produces coherent, personal-feeling summaries with minimal prompt engineering.

## Service-Specific Patterns

**Route-handler naming** — convention requires a verb prefix on all handler functions: `get_`, `create_`, `update_`, `delete_`. Defined in `code-conventions`.

**Pydantic schemas alongside endpoints** — response and request models are Pydantic classes defined in the same endpoint module or a peer `schemas/` file. FastAPI's native validation is the only input validation layer.

**HTTPException for error paths** — error responses use `raise HTTPException(status_code=..., detail=...)` directly; silent exception swallowing (bare `except` returning an error dict) is explicitly prohibited by convention.

**Dependency declaration before import** — any new dependency must be declared in `requirements.txt` before importing the library. Importing an undeclared package fails in a fresh virtualenv or CI. Current declared deps: `fastapi>=0.110.0`, `uvicorn[standard]>=0.29.0`, `pytest>=8.0.0`, `httpx>=0.27.0`, `ruff>=0.4.0`.

**Testing via FastAPI TestClient** — tests live in `fanfest/backend/tests/test_{domain}.py`, use `fastapi.testclient.TestClient`, and mock external third-party APIs (Anthropic, Google) to avoid billing and flakiness. Shared fixtures go in `tests/conftest.py`. `test_health.py` covers `GET /health`; `test_events.py` covers all five FEST-02 BDD scenarios (9 test functions). `pyproject.toml` sets `pythonpath = ["."]` so `from app.main import app` resolves when pytest runs from `fanfest/backend/`.
