---
document_type: architecture
summary: >-
  FanFest is a single-repository project (not a monorepo) containing two runtime
  components under a shared `fanfest/` directory. There is no workspace tool,
  no...
last_updated: '2026-06-19T18:35:00.000Z'
tags:
  - architecture
  - topology
  - python
  - fastapi
---
# Architecture

## Monorepo / Repository Shape

FanFest is a single-repository project (not a monorepo) containing two runtime components under a shared `fanfest/` directory. There is no workspace tool, no monorepo configuration file (no `pnpm-workspace.yaml`, `lerna.json`, `nx.json`, or equivalent), and no build graph linking the two components. Each component is independently started with its own shell command.

The top-level layout is flat: `fanfest/backend/` holds the Python service and `fanfest/frontend/` holds all browser-delivered assets. Alongside these sit documentation, a root `README.md`, project metadata, and `.github/workflows/` for CI. No Makefile and no task runner are present.

| Workspace / Directory | Language | Role |
|-----------------------|----------|------|
| `fanfest/backend/` | Python | FastAPI HTTP API, AI recap generation |
| `fanfest/frontend/` | JavaScript / HTML / CSS | Vanilla JS SPA, browser client |
| `docs/` | Markdown | Project documentation and wiki |

---

## Service Inventory

| ID | Type | Language | Port | Role |
|----|------|----------|------|------|
| [[backend]] | backend | Python (FastAPI) | 8000 | REST API; AI recap via Claude; planned Google integrations |
| [[frontend]] | frontend | JavaScript (vanilla) | 8080 | Single-page app served via `python -m http.server` |

The backend follows a layered layout (`app/api/v1/endpoints/`, `app/core/`, `app/models/`, `app/schemas/`, `app/services/`). As of FEST-03 the core app is bootstrapped with a working FastAPI instance, CORSMiddleware, and an events domain (`endpoints/events.py`, `schemas/events.py`, `services/match_state.py`, `services/photos_service.py`, `services/registry.py`). The frontend is five JS/CSS files: one HTML entry point, two JS application modules (`main.js` for Feature 01 discovery, `live.js` for live event + Hype Wall), one shared API client (`api.js`), and two CSS stylesheets.

---

## Service Communication

The only inter-service channel is browser-to-backend HTTP. The frontend's `fanfest/frontend/assets/js/api.js` module issues `fetch()` calls to the backend at `http://localhost:8000`. No WebSocket, gRPC, message queue, or event-bus channel exists.

| Source | Target | Protocol | Notes |
|--------|--------|----------|-------|
| frontend (`api.js`) | backend (`app/main.py`) | HTTP / REST | JSON request/response; active endpoints: `GET/POST /api/v1/events/{id}/match-state`, `POST/GET /api/v1/events/{id}/photos` |

No backend-to-frontend push channel (SSE, WebSocket) has been implemented. No service mesh, proxy, or API gateway sits between the two.

---

## External Integrations

Three external vendors are declared via environment variables; no in-repo client wrapper beyond the `ANTHROPIC_API_KEY` usage has been scaffolded for the Google integrations.

| Vendor | Purpose | In-repo client path | Auth mechanism | Environments |
|--------|---------|---------------------|----------------|--------------|
| Anthropic (Claude API) | AI-generated post-event recap narrative | (not determined by analysis) | Bearer API key via `ANTHROPIC_API_KEY` env var | local; production (not determined by analysis) |
| Google OAuth | User authentication (planned) | (not determined by analysis) | OAuth 2.0 client credentials via env vars | local; production (not determined by analysis) |
| Google Calendar API | Calendar integration (planned) | (not determined by analysis) | Google OAuth token (same credential set) | local; production (not determined by analysis) |
| Google Maps API | Maps integration (planned) | (not determined by analysis) | Google OAuth token (same credential set) | local; production (not determined by analysis) |
| Google Drive API | Hype Wall photo storage | `app/services/photos_service.py` | Service-account JSON via `GOOGLE_SERVICE_ACCOUNT_FILE` env var; falls back to in-memory mock when unset | local; production (not determined by analysis) |

All Google integrations except Drive are indicated only by environment variable names in `.env.example`. Google Drive now has a service wrapper (`app/services/photos_service.py`) using `google-api-python-client`; it operates in mock/in-memory mode when `GOOGLE_SERVICE_ACCOUNT_FILE` is unset, switching to live Drive when credentials are present.

---

## Authentication & Authorisation

No authentication or authorisation implementation exists in the codebase. Google OAuth is declared as the intended identity provider, evidenced by the required Google credential environment variables listed in the README and `.env.example`. The full auth flow (token exchange, session minting, route protection, role registry) has not been designed or scaffolded.

When implemented, the expected shape is standard OAuth 2.0 Authorization Code flow: the frontend redirects to Google, Google returns an authorization code, the backend exchanges it for an access token and ID token, and the backend issues a session token to the browser. None of this logic is present today.

---

## Request Lifecycle

**Browser request for event recap (primary path):**

1. User interacts with the SPA (`fanfest/frontend/index.html` bootstraps `assets/js/main.js`).
2. `main.js` calls a function in `assets/js/api.js` to POST event details to the backend.
3. `api.js` issues `fetch('http://localhost:8000/...')` with a JSON body.
4. The FastAPI router in `fanfest/backend/app/main.py` matches the route and dispatches to a handler (exact handler path not determined by analysis).
5. The handler calls the Anthropic Claude API with event context to generate a recap narrative.
6. The backend returns the generated text as a JSON response.
7. `api.js` resolves the promise; `main.js` renders the recap into the DOM.

**Static asset request:**

1. Browser requests `index.html`, CSS, or JS files.
2. `python -m http.server 8080` serves the file directly from `fanfest/frontend/`.
3. No server-side rendering, no build step, no cache headers beyond Python's defaults.

---

## Data Architecture

No operational data store has been declared. No database, cache, message queue, or object store is present or referenced anywhere in the codebase. No ORM (SQLAlchemy, Tortoise, etc.), no migration tool (Alembic, etc.), and no schema definition file exist.

No durable database or object store has been declared. All state is in-memory: match state and Hype Wall photos are held in module-level Python dicts in `services/match_state.py` and `services/photos_service.py` and reset on server restart. If persistence is added, the scaffolded `app/models/` and `app/schemas/` directories provide the intended placement.

| Store | Technology | Status |
|-------|-----------|--------|
| Primary database | (not determined by analysis) | Not implemented |
| Cache | (not determined by analysis) | Not implemented |
| Queue | (not determined by analysis) | Not implemented |

---

## Deployment Topology

No deployment configuration exists. No `Dockerfile`, `docker-compose.yml`, Kubernetes manifest, Cloud Run service definition, or serverless function configuration is present in the repository. The project runs exclusively via manual shell commands documented in the README.

| Target | Service | Trigger |
|--------|---------|---------|
| Local machine | backend (port 8000) | `uvicorn app.main:app --reload` (manual) |
| Local machine | frontend (port 8080) | `python -m http.server 8080` (manual) |
| Cloud / production | (not determined by analysis) | (not determined by analysis) |

---

## Local Development

No Docker Compose, no Makefile, no task runner. A developer runs the full local stack with two terminal sessions:

```bash
# Terminal 1 — backend
cd fanfest/backend
pip install -r requirements.txt
cp .env.example .env          # fill ANTHROPIC_API_KEY and Google credentials
uvicorn app.main:app --reload
# API at http://localhost:8000
```

```bash
# Terminal 2 — frontend
cd fanfest/frontend
python -m http.server 8080
# Open http://localhost:8080
```

No emulators (Firebase, DynamoDB Local, etc.) are required because no database or external stateful service has been implemented. The only required credential for the core feature is `ANTHROPIC_API_KEY`; Google credentials are needed only if the planned integrations are exercised.

---

## Automation & CI

GitHub Actions CI is configured at `.github/workflows/ci.yml`. The workflow triggers on every `push` and `pull_request` with `permissions: contents: read` (least privilege) and runs two parallel jobs.

| Job | Runner | Steps |
|-----|--------|-------|
| `backend` | `ubuntu-latest` | checkout → Python 3.12 setup → `pip install -r requirements.txt` → `ruff check .` → `pytest` |
| `frontend` | `ubuntu-latest` | checkout → `node --check fanfest/frontend/assets/js/main.js` |

All third-party actions are pinned to major version tags (`actions/checkout@v4`, `actions/setup-python@v5`). The backend job uses `defaults.run.working-directory: fanfest/backend` so all commands resolve relative to the backend root. Local operations continue to be raw shell commands documented in `README.md`.

| Concern | Tool | Status |
|---------|------|--------|
| Dependency install | `pip install -r requirements.txt` | CI + manual |
| Backend server | `uvicorn` | Manual |
| Frontend server | `python -m http.server` | Manual |
| Test runner | `pytest` (backend) | CI + manual |
| CI pipeline | GitHub Actions | Configured |
| Linting | `ruff check .` | CI + manual |

---

## Coupling Hotspots

The graph detects frontend JS render functions as the dominant hub/bridge cluster. The backend's events domain (`endpoints/events.py`, `services/match_state.py`, `services/photos_service.py`) is now implemented; backend coupling hotspots will be visible in future graph refreshes.

**Hubs** (highest total degree, largest blast radius on change — frontend):

- `fanfest/frontend/assets/js/main.js::$` (Feature 01 DOM query helper — widest reach)
- `fanfest/frontend/assets/js/main.js::renderSeleccion`, `tags`, `renderCategories`, `renderWorld`

**Backend note:** `app/api/v1/endpoints/events.py` is the primary entry point for the events domain; `app/services/photos_service.py` and `app/services/match_state.py` are its dependencies. Changes to the events endpoint shape ripple to the frontend `api.js` client.
