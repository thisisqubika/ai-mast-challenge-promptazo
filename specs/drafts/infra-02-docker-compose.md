# Infra 02 — Docker & docker compose up

**Track:** Infra / DevOps · **Risk hint:** LOW · **Strategy:** DIRECT
**Depends on:** infra-01 (backend health app must exist)
**Decision context:** approved to add Docker now for the Delivery-Requirements extra points ("`docker compose up` levanta todo"). Backend service stays minimal until product fills it.

## Description

Containerize the app so a judge can clone the repo and run everything with one
command. Backend runs in its own image; the static frontend is served alongside.

- `fanfest/backend/Dockerfile`: `python:3.12-slim`, install `requirements.txt`, run `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- `docker-compose.yml` (repo root):
  - `backend` — built from `fanfest/backend`, exposes `8000`.
  - `frontend` — serves `fanfest/frontend` as static files (e.g. `nginx:alpine` or a tiny static server) on `8080`.
- `.dockerignore` to keep images lean (no `.git`, `__pycache__`, `node_modules`, etc.).

## Acceptance Criteria

- [ ] `docker compose up` starts both services with no manual steps.
- [ ] Frontend (Tribuna Home) is reachable at `http://localhost:8080`.
- [ ] Backend health is reachable at `http://localhost:8000/health` → `{"status": "ok"}`.
- [ ] Images build cleanly from a fresh clone (no cached layers required).
- [ ] `.dockerignore` excludes VCS, caches, and secrets.
- [ ] README documents `docker compose up` and the two URLs.

## Notes

- No secrets baked into images. Backend reads config from env (`.env` is gitignored; document vars in `.env.example`).
- Apply QAF skills: `developing-with-docker`.
- Keep it minimal — this is the demo-friendliness artifact, not a production deployment.
