---
document_type: service
summary: >-
  The backend is a Python FastAPI server (port 8000) that acts as the sole API
  layer for the FanFest platform. It is responsible for serving the REST API
  consu...
last_updated: '2026-06-19T18:50:00.000Z'
tags:
  - service
  - python
  - backend
  - fastapi
service_id: backend
---
# Fan Fest Backend

## Purpose

The backend is a Python FastAPI server (port 8000) that acts as the sole API layer for the FanFest platform. It is responsible for serving the REST API consumed by the [[frontend]], proxying all calls to external third-party services (Anthropic, Google), and owning the AI-generated event recap feature. The app is fully bootstrapped: `requirements.txt` is populated, `main.py` runs with CORSMiddleware, and the events domain exposes endpoints for detail, predictions, check-in, live match state, and Hype Wall photos.

## Public API / Surface

All routes are under `app/api/v1/endpoints/events.py`, mounted at `/api/v1`:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Infrastructure health probe; no auth required |
| `GET` | `/api/v1/events/{id}` | Full event detail: teams, venue, time, organizer, attendees, invite/calendar/maps links |
| `POST` | `/api/v1/events/{id}/predictions` | Submit or overwrite a per-user scoreline (0–9); locked (HTTP 409) after mocked match-start time |
| `POST` | `/api/v1/events/{id}/checkin` | Mark user present (idempotent); HTTP 400 if no user identity supplied |
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
│   └── services/             # business logic
└── tests/                    # pytest test suite
```

`app/main.py` contains the live FastAPI app. `api/v1/endpoints/events.py` is the product-domain endpoint module; `schemas/events.py` holds all Pydantic models. The `services/` layer has four active modules: `events_service.py` (event detail, predictions, check-in store), `match_state.py` (in-memory mocked match state with goal/end/reset actions), `photos_service.py` (Google Drive wrapper with in-memory mock fallback), `registry.py` (mock check-in registry for upload authorization). `models/` remains unimplemented. No ORM, database client, or migration tool has been declared.

## Request Lifecycle

1. HTTP request arrives at uvicorn on port 8000
2. `CORSMiddleware` in `main.py` validates the `Origin` header (default allow: `http://localhost:8080`)
3. FastAPI routes to the matching handler in `api/v1/endpoints/events.py`
4. Handler calls into `services/` for business logic
5. For photo uploads: `registry.is_checked_in(uploader_id)` is checked; `HTTPException(403)` raised if not
6. Response serialized via Pydantic schema from `schemas/events.py` and returned

CORS origins are configured via `CORS_ORIGINS` env var (default `http://localhost:8080`) in `app/core/config.py`.

## Data Layer

State lives in module-level Python dicts across multiple service modules; all reset on server restart.

| Store | Module | Key | Value |
|-------|--------|-----|-------|
| `_events` | `events_service.py` | `event_id: str` | event detail dict (seeded with mock event `evt-001`) |
| `_predictions` | `events_service.py` | `(user_id, event_id): tuple` | prediction dict `{user_id, event_id, home_score, away_score}` |
| `_attendees` | `events_service.py` | `event_id: str` | `set[str]` of checked-in user IDs |
| `_states` | `match_state.py` | `event_id: str` | `MatchState` (score, status, clock, goals) |
| `_photos` | `photos_service.py` | `event_id: str` | list of `Photo` dicts |

When `GOOGLE_SERVICE_ACCOUNT_FILE` is set, photo files are stored in Google Drive (`GOOGLE_DRIVE_FOLDER_ID`); otherwise photos are held in memory only. No external database, ORM, cache, or object store.

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

**Dependency declaration before import** — add any new dependency to `requirements.txt` before importing. CI installs from this file; missing entries cause import errors in GitHub Actions even if locally installed.

**Testing via FastAPI TestClient** — tests live in `fanfest/backend/tests/test_{domain}.py`, use `fastapi.testclient.TestClient`, and mock external third-party APIs (Anthropic, Google) to avoid billing and flakiness. Shared fixtures go in `tests/conftest.py`. `test_health.py` covers `GET /health`; `test_events.py` covers all FEST-02 BDD scenarios (9 tests) and FEST-03 match-state/photos scenarios. `pyproject.toml` sets `pythonpath = ["."]` so `from app.main import app` resolves when pytest runs from `fanfest/backend/`.
