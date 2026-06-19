# Infra 01 — CI Pipeline + Backend Health Endpoint

**Track:** Infra / DevOps · **Risk hint:** LOW · **Strategy:** DIRECT
**Depends on:** nothing · **Enables:** infra-02 (Docker), infra-03 (deploy)
**Decision context:** approved to add a minimal backend so CI runs green instead of hollow. Pure infra, no product logic — product/QAF own real features later.

## Description

Stand up continuous integration on GitHub Actions and give it something real to
verify: a minimal FastAPI backend exposing a health endpoint. This unblocks
Docker (infra-02) and a real backend deploy, and gives the team a green pipeline
to build features against while product finishes definitions.

**Backend (minimal, infra-only):**
- `fanfest/backend/app/main.py`: FastAPI app with `GET /health` → `{"status": "ok"}`.
- `fanfest/backend/requirements.txt`: `fastapi`, `uvicorn[standard]`, plus dev deps `pytest`, `httpx`, `ruff`.
- `fanfest/backend/tests/test_health.py`: asserts `/health` returns 200 and the expected payload.

**CI workflow** (`.github/workflows/ci.yml`), on `push` and `pull_request`:
- **backend** job: set up Python 3.12, install requirements, `ruff check`, `pytest`.
- **frontend** job: lightweight static validation — `node --check` on `assets/js/main.js` (no framework, no build step).

## Acceptance Criteria

- [ ] `GET /health` returns `200` with body `{"status": "ok"}`.
- [ ] `pytest` passes locally and in CI; at least the health test exists.
- [ ] `ruff check` passes on the backend with zero warnings.
- [ ] `.github/workflows/ci.yml` runs on push and PR, with backend + frontend jobs.
- [ ] Both CI jobs pass green on the current `main`.
- [ ] Workflow uses least-privilege `permissions: { contents: read }` and pins actions to a major version (or SHA).

## Notes

- Keep the backend strictly infra: only `/health`. Product features arrive via the product drafts + QAF.
- Apply QAF skills: `github-actions-secure-ci-cd-pipelines`, `pytest-patterns`.
- Python 3.12. Run commands from `fanfest/backend`.
