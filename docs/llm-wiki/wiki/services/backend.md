---
document_type: service
summary: >-
  The backend is a Python FastAPI server (port 8000) that acts as the sole API
  layer for the FanFest platform. It is responsible for serving the REST API
  consu...
last_updated: '2026-06-19T18:35:00.000Z'
tags:
  - service
  - python
  - backend
  - fastapi
service_id: backend
---
# Fan Fest Backend

## Purpose

The backend is a Python FastAPI server (port 8000) that acts as the sole API layer for the FanFest platform. It is responsible for serving the REST API consumed by the [[frontend]], proxying all calls to external third-party services (Anthropic, Google), and owning the AI-generated event recap feature. As of FEST-03 the app is fully bootstrapped: `requirements.txt` is populated, `main.py` runs with CORSMiddleware, and the events domain exposes four routes.

## Public API / Surface

All routes are under `app/api/v1/endpoints/events.py`, mounted at `/api/v1`:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/events/{id}/match-state` | Returns live scoreboard, clock, venue, goals list |
| `POST` | `/api/v1/events/{id}/match-state` | Dev control: advance state (`action: goal|end|reset`) |
| `POST` | `/api/v1/events/{id}/photos` | Upload Hype Wall photo (multipart); 403 if uploader not checked in |
| `GET` | `/api/v1/events/{id}/photos` | List all photos with uploader identity |

FastAPI auto-generates OpenAPI docs at `/docs` and `/redoc`. Route handlers follow the `get_`/`create_`/`update_`/`delete_` verb-prefix convention.

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

The `services/` layer has three active modules: `match_state.py` (in-memory mocked match state with goal/end/reset actions), `photos_service.py` (Google Drive wrapper with in-memory mock fallback), `registry.py` (mock check-in registry for upload authorization). `models/` remains unimplemented; `schemas/events.py` holds all Pydantic models. No ORM, database client, or migration tool has been declared.

## Request Lifecycle

1. HTTP request arrives at uvicorn on port 8000
2. `CORSMiddleware` in `main.py` validates the `Origin` header (default allow: `http://localhost:8080`)
3. FastAPI routes to the matching handler in `api/v1/endpoints/events.py`
4. Handler calls into `services/` (`match_state`, `photos_service`, `registry`) for business logic
5. For photo uploads: `registry.is_checked_in(uploader_id)` is checked; `HTTPException(403)` raised if not
6. Response serialized via Pydantic schema from `schemas/events.py` and returned

CORS origins are configured via `CORS_ORIGINS` env var (default `http://localhost:8080`) in `app/core/config.py`.

## Data Layer

No database, ORM, or durable store has been declared. State lives in module-level Python dicts in `services/match_state.py` (match state per event) and `services/photos_service.py` (photo metadata per event); both reset on server restart. When `GOOGLE_SERVICE_ACCOUNT_FILE` is set, photo files are stored in Google Drive (`GOOGLE_DRIVE_FOLDER_ID`); otherwise photos are held in memory only.

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

**Dependency declaration before import** — add any new dependency to `requirements.txt` before importing. The venv at `fanfest/backend/.venv/` currently declares: `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `python-multipart`, `google-auth`, `google-api-python-client`, `pytest`, `httpx`.

**Testing via FastAPI TestClient** — tests live in `fanfest/backend/tests/test_{domain}.py`, use `fastapi.testclient.TestClient`, and mock external third-party APIs (Anthropic, Google) to avoid billing and flakiness. Shared fixtures go in `tests/conftest.py`. 8 tests exist in `tests/test_events.py` covering the events domain.
