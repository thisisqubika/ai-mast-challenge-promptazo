---
document_type: service
summary: >-
  The backend is a Python FastAPI server (port 8000) that acts as the sole API
  layer for the FanFest platform. It is responsible for serving the REST API
  consu...
last_updated: '2026-06-19T16:01:37.120Z'
tags:
  - service
  - python
  - backend
  - fastapi
service_id: backend
---
# Fan Fest Backend

## Purpose

The backend is a Python FastAPI server (port 8000) that acts as the sole API layer for the FanFest platform. It is responsible for serving the REST API consumed by the [[frontend]], proxying all calls to external third-party services (Anthropic, Google), and owning the AI-generated event recap feature. At the time of scaffolding the backend is a complete directory skeleton with no implemented logic; all Python source files are empty stubs and `requirements.txt` is blank.

## Public API / Surface

(not determined by analysis) — no routes have been implemented yet. The intended pattern from `code-conventions` places all route handlers under `fanfest/backend/app/api/v1/endpoints/{domain}.py`, each domain in its own module, routers registered in `fanfest/backend/app/main.py` via `app.include_router(router)`. When routes exist, FastAPI auto-generates OpenAPI docs at `/docs` and `/redoc`.

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

All subdirectories are empty stubs. No ORM, auth library, database client, or migration tool has been declared. The structure establishes placement conventions without constraining future implementation choices.

## Request Lifecycle

All backend Python files are 1-line empty stubs. No handlers, middleware, or routes exist. Intended lifecycle once implemented:

1. HTTP request arrives at uvicorn on port 8000
2. FastAPI routes to the matching handler in `api/v1/endpoints/{domain}.py`
3. Handler calls into `services/` for business logic
4. Service calls external APIs (Anthropic, Google) using credentials from env vars
5. Response serialized via Pydantic schema and returned

CORS must be configured in `main.py` because the [[frontend]] runs on a separate origin (port 8080) with no reverse proxy in local development.

## Data Layer

(not determined by analysis) — no database, ORM, cache, or object store has been declared or configured. No DB client appears in `requirements.txt` (which is empty). Persistence layer is entirely unimplemented.

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

**Dependency declaration before import** — because `requirements.txt` starts blank, any new dependency must be added there before importing the library. Importing an undeclared package fails in a fresh virtualenv.

**Testing via FastAPI TestClient** — tests live in `fanfest/backend/tests/test_{domain}.py`, use `fastapi.testclient.TestClient`, and mock external third-party APIs (Anthropic, Google) to avoid billing and flakiness. Shared fixtures go in `tests/conftest.py`. No tests exist yet.
