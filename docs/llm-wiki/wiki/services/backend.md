---
document_type: service
summary: >-
  The backend is a Python FastAPI server (port 8000) that acts as the sole API
  layer for the FanFest platform. It is responsible for serving the REST API
  consu...
last_updated: '2026-06-19T19:45:00.000Z'
tags:
  - service
  - python
  - backend
  - fastapi
service_id: backend
---
# Fan Fest Backend

## Purpose

The backend is a Python FastAPI server (port 8000) that acts as the sole API layer for the FanFest platform. It is responsible for serving the REST API consumed by the [[frontend]], proxying all calls to external third-party services (Anthropic, Google), and owning the AI-generated event recap feature. As of FEST-04 the app is fully bootstrapped: `requirements.txt` is populated, `main.py` runs with CORSMiddleware, and the events domain exposes five routes including the AI-powered recap endpoint.

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
| `POST` | `/api/v1/events/{id}/recap` | Generate AI-powered event recap; 409 if match not ended; 200 with `fallback: true` on Anthropic failure |

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

**Dependency declaration before import** — add any new dependency to `requirements.txt` before importing. CI installs from this file; missing entries cause import errors in GitHub Actions even if locally installed. The venv at `fanfest/backend/.venv/` currently declares: `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `python-multipart`, `google-auth`, `google-api-python-client`, `anthropic`, `pytest`, `httpx`, `ruff`.

**Testing via FastAPI TestClient** — tests live in `fanfest/backend/tests/test_{domain}.py`, use `fastapi.testclient.TestClient`, and mock external third-party APIs (Anthropic, Google) to avoid billing and flakiness. Shared fixtures go in `tests/conftest.py`. 17 tests exist: 10 in `tests/test_events.py` + `tests/test_health.py` (events domain and health), 7 in `tests/test_recap.py` (recap endpoint: happy path, fallback, empty-key fallback, 409/404/422 errors, slide_count cap).
