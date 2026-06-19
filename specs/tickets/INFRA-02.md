# INFRA-02: Containerize FanFest so `docker compose up` starts the whole app

## 📋 User Story

**As a** challenge judge (or new contributor) cloning the FanFest repository
**I want** to start the backend and frontend with a single `docker compose up` command
**So that** I can evaluate the running application immediately, with no manual environment setup or per-service install steps.

---

## 👥 Stakeholders

| Role | Name | Responsibility |
|------|------|----------------|
| Requester / Tech Lead | Sebastian Demasi (SRE / DevOps) | Authored the draft, owns infra, technical approval |
| End Users | Challenge judges, new contributors | Run the app from a fresh clone with one command |
| Related Owners | Product / QAF | Fill in real backend product logic later (out of scope here) |

---

## 🎯 Success Criteria

1. From a fresh clone, `docker compose up` starts both services with zero manual steps and no pre-built/cached layers required.
2. The frontend (Tribuna Home) is reachable at `http://localhost:8080`.
3. The backend health endpoint is reachable at `http://localhost:8000/health` and returns `{"status": "ok"}`.
4. No secrets are baked into any image; backend configuration is read from the environment, with variables documented in `.env.example`.
5. README documents the `docker compose up` flow and both URLs.

**Metrics**: Time-to-running-app from a fresh clone is a single command; both images build cleanly from scratch (`docker compose build --no-cache` succeeds); image size stays lean thanks to `.dockerignore`.

---

## ✅ Acceptance Criteria

### Scenario 1: Happy Path — one command brings up the full stack
```gherkin
Given a fresh clone of the repository on a machine with Docker installed
And a valid .env file derived from fanfest/backend/.env.example
When the user runs "docker compose up" from the repository root
Then the backend service builds from fanfest/backend and listens on port 8000
And the frontend service serves fanfest/frontend as static files on port 8080
And no manual install or build step is required beyond the single command
```

### Scenario 2: Backend health is reachable in the container
```gherkin
Given the stack is running via "docker compose up"
When the user requests "http://localhost:8000/health"
Then the response status is 200
And the response body is {"status": "ok"}
```

### Scenario 3: Frontend is reachable in the container
```gherkin
Given the stack is running via "docker compose up"
When the user opens "http://localhost:8080" in a browser
Then the Tribuna Home page (fanfest/frontend/index.html) is served
And its static assets under assets/ load without 404s
```

### Scenario 4: Images build from a clean cache
```gherkin
Given a fresh clone with no Docker build cache
When the user runs "docker compose build --no-cache"
Then both the backend and frontend images build successfully with no errors
```

### Scenario 5: Build context excludes VCS, caches, and secrets
```gherkin
Given the .dockerignore file at the relevant build context root
When an image is built
Then .git, __pycache__, .venv, node_modules, and any .env file are excluded from the build context
And no secret values are present in the resulting image layers
```

### Scenario 6: Backend stops cleanly on shutdown (PID 1 signal handling)
```gherkin
Given the stack is running via "docker compose up"
When the user sends an interrupt (Ctrl+C) or "docker compose down"
Then the backend container receives the termination signal at PID 1
And uvicorn shuts down gracefully without requiring a forced kill
```

---

## 🔧 Technical Context

### Current State
- Backend FastAPI app scaffold exists at `fanfest/backend/app/` (entry `app/main.py`); the `/health` endpoint and `requirements.txt` are delivered by INFRA-01 and are prerequisites of this ticket.
- Frontend is static, no bundler: `fanfest/frontend/index.html` plus `assets/css/`, `assets/js/` (`main.js`, `api.js`).
- No `Dockerfile`, `docker-compose.yml`, or `.dockerignore` exists in the FanFest app today.
- Backend runs locally via `uvicorn app.main:app --reload` from `fanfest/backend`; frontend via `python -m http.server 8080` from `fanfest/frontend` (per README).
- Services and ports are fixed: backend `8000`, frontend `8080` (per project CLAUDE.md Services & Ports table).
- `.env` is gitignored (`*.env`, with `!.env.example` retained); `fanfest/backend/.env.example` documents `ANTHROPIC_API_KEY` and Google OAuth credentials.

### Proposed Changes
- `fanfest/backend/Dockerfile`: base `python:3.12-slim`; copy and `pip install -r requirements.txt`; run `uvicorn app.main:app --host 0.0.0.0 --port 8000` using the exec form so uvicorn is PID 1 and receives signals directly.
- `docker-compose.yml` at the repo root with two services:
  - `backend` — built from `fanfest/backend`, exposes `8000`; reads config from the environment (`env_file: ./fanfest/backend/.env` or compose `environment:`).
  - `frontend` — serves `fanfest/frontend` as static files on `8080` (e.g. `nginx:alpine` mounting/copying the static dir, or a minimal static server).
- `.dockerignore` to keep the build context and images lean: exclude `.git`, `__pycache__`, `*.py[cod]`, `.venv`/`venv`, `.pytest_cache`, `.ruff_cache`, `node_modules`, and any `.env` files.
- README update: a "Run with Docker" section documenting `docker compose up`, `http://localhost:8080` (frontend), and `http://localhost:8000/health` (backend).

### Technical Constraints
- No secrets baked into images. Backend reads config from env; `.env` stays gitignored, variables documented in `.env.example`.
- Keep it minimal — this is the demo-friendliness artifact, not a production deployment. No orchestration, registries, multi-stage prod optimization, or TLS.
- Bind the backend to `0.0.0.0` (not `127.0.0.1`) so the published port is reachable from the host.
- Backend uvicorn must run as PID 1 via the exec form so SIGTERM/SIGINT reach it for graceful shutdown.
- Container stdout/stderr must remain unbuffered so logs surface in `docker compose logs`.

### Integration Points
- Backend health endpoint `GET /health` from INFRA-01 (the verification target inside the container).
- Frontend `assets/js/api.js` points the browser at `http://localhost:8000` for backend calls; the published host ports must match so cross-service browser requests resolve.
- Environment contract defined by `fanfest/backend/.env.example`.

### Architecture Decisions
- **Two separate images/services (backend + frontend), not a single combined image.** Rationale: matches the project's service/port model (8000 / 8080), keeps each concern independently buildable, and mirrors the local run model.
- **`python:3.12-slim` for the backend.** Rationale: Python 3.12 is the project standard (INFRA-01, CLAUDE.md); `slim` keeps the image lean for a demo artifact.
- **Static frontend served by a tiny static server (`nginx:alpine` or equivalent).** Rationale: vanilla JS with no build step needs only static file serving; `nginx:alpine` is small and reliable.
- **Config via environment, never baked secrets.** Rationale: required by project conventions and the draft; keeps images shareable and `.env` gitignored.

---

## 🚫 Out of Scope

The following are explicitly NOT part of this ticket:
1. Implementing or expanding backend product logic — the backend stays minimal (`/health` from INFRA-01) until product/QAF deliver features.
2. Production deployment, hosting, container registries, or CI image publishing (frontend deploy is INFRA-03).
3. Multi-stage production-optimized builds, TLS/HTTPS, reverse-proxy hardening, or non-root user hardening beyond what a minimal demo needs.
4. Database, cache, or any additional service in the compose file.
5. Live-reload / bind-mount developer workflow inside containers.

**Future Considerations**: A production-grade multi-stage build, non-root container user, healthcheck-driven `depends_on` conditions, and pushing images to a registry could follow once the app moves past the demo stage.

---

## ⚠️ Edge Cases & Error Handling

### Edge Cases
1. **Missing `.env` file**: `docker compose up` should still start; backend uses safe defaults where possible and only fails on a feature that genuinely needs a secret (e.g. AI recap). Document that `.env` is copied from `.env.example` for full functionality.
2. **Port already in use (8000 or 8080)**: Docker surfaces a clear bind error; README notes the two ports must be free.
3. **Stale build cache hiding a broken Dockerfile**: validated by `docker compose build --no-cache` (Scenario 4) so a fresh-clone judge is never blocked by local cache.
4. **Frontend requesting backend before it is ready**: backend boot is fast; if needed, `depends_on` orders startup, though browser calls tolerate a brief backend warm-up.

### Error Scenarios
1. **Backend image fails to build (missing/blank `requirements.txt`)**: build fails fast with the pip error; resolved by completing INFRA-01 first (the blocking dependency).
2. **Health endpoint unreachable after startup**: indicates the app bound to `127.0.0.1` or wrong port — verify `--host 0.0.0.0 --port 8000` and the published port mapping.
3. **Container exits immediately (PID 1 / signal mishandling)**: use the exec form for the uvicorn command so the process is PID 1 and handles signals.

### Data Validation Rules
- `.dockerignore` must exclude all VCS, cache, virtualenv, node, and `.env` artifacts.
- No `.env`, credential, or token value may appear in any committed Dockerfile, compose file, or image layer.
- Backend listen address must be `0.0.0.0:8000`; frontend served on `8080`.

---

## 📦 Dependencies

### Blocking
- [ ] INFRA-01 — CI Pipeline + Backend Health Endpoint (the FastAPI `/health` app and `requirements.txt` must exist before the backend image can build).

### Related
- INFRA-03 — Deploy frontend (GitHub Pages) — consumes the same static `fanfest/frontend/` artifact this ticket containerizes.

---

## 🎓 Definition of Done

### Code Quality
- [ ] All acceptance criteria scenarios implemented
- [ ] `fanfest/backend/Dockerfile`, root `docker-compose.yml`, and `.dockerignore` added
- [ ] Backend command uses exec form, binds `0.0.0.0:8000`, runs unbuffered
- [ ] No secrets committed in any Docker/compose artifact

### Testing
- [ ] `docker compose up` from a fresh clone starts both services with no manual steps
- [ ] `curl http://localhost:8000/health` returns 200 with `{"status": "ok"}`
- [ ] `http://localhost:8080` serves Tribuna Home with assets loading
- [ ] `docker compose build --no-cache` succeeds for both images
- [ ] `docker compose down` / Ctrl+C shuts the backend down gracefully
- [ ] `.dockerignore` verified to exclude VCS, caches, `.venv`, `node_modules`, and `.env`

### Documentation
- [ ] README updated with a "Run with Docker" section: `docker compose up` plus both URLs
- [ ] `.env.example` documents required backend variables (no real values)

### Review & Deployment
- [ ] Code reviewed and approved
- [ ] PR merged to main
- [ ] A reviewer validated the one-command run from a fresh clone

---

## 📝 Implementation Notes

- Apply the QAF `developing-with-docker` skill. Key prescriptive points for this ticket:
  - Run uvicorn via the exec form so it is **PID 1** and receives SIGTERM/SIGINT (clean `docker compose down`).
  - Bind to `0.0.0.0`, not `127.0.0.1`, or the published port will not be reachable from the host.
  - Keep stdout/stderr unbuffered so logs appear in `docker compose logs`.
  - Keep the build context small via `.dockerignore` (faster builds, leaner images).
  - If startup ordering matters, prefer `depends_on` with readiness in mind; a simple ordering is sufficient for this demo.
- Follow the project multi-file workflow for a new backend dependency: any package must be pinned in `fanfest/backend/requirements.txt` before it is imported (INFRA-01 owns the base set: `fastapi`, `uvicorn[standard]`).
- The backend app entry is `app.main:app` and commands run from `fanfest/backend` (per README and CLAUDE.md).
- Keep this minimal: it is the "`docker compose up` levanta todo" demo-friendliness artifact for the Delivery-Requirements extra points, not a production deployment.

---

## 🔗 References

- Draft: `specs/drafts/infra-02-docker-compose.md`
- Dependency draft: `specs/drafts/infra-01-ci-and-backend-health.md`
- Project conventions: `.claude/CLAUDE.md` (Services & Ports, File Placement Guide)
- QAF skill: `qubika-agentic-framework/skills/070-infrastructure/developing-with-docker`
- Run-locally reference: `README.md` § How to Run It Locally

---

**Created**: 2026-06-19
**Created By**: Claude (create-sdd-ticket skill)
**INVEST Validated**: ✅
**BDD Scenarios**: 6
**Priority**: Medium
**Labels**: sdd, infra, devops, docker
