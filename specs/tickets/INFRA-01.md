# INFRA-01: CI Pipeline + Backend Health Endpoint

## User Story

**As a** FanFest team member  
**I want** a green GitHub Actions CI pipeline backed by a real FastAPI health endpoint  
**So that** the team has a verified baseline to build product features against and Docker + deploy work (infra-02, infra-03) is unblocked

## Stakeholders

- Engineering team — implementer and primary audience; needs green CI before layering on Docker and deploy
- Product / QAF — consumers of the green pipeline; product features land after this baseline is in place

## Success Criteria

1. `GET /health` returns HTTP 200 with body `{"status": "ok"}` from a running local server and in CI.
2. `pytest` finds and passes `tests/test_health.py` both locally and in the CI backend job.
3. `ruff check` exits 0 (zero warnings) on the backend codebase in CI.
4. `.github/workflows/ci.yml` runs on every `push` and `pull_request` event, with distinct `backend` and `frontend` jobs, both passing green on the current `main` branch.
5. The CI workflow uses `permissions: { contents: read }` and all third-party actions are pinned to a major version or SHA.

## Acceptance Criteria

### Scenario 1: Health endpoint returns expected payload

```gherkin
Given the FastAPI backend is running locally (`uvicorn app.main:app --reload`)
When I send GET /health
Then the response status is 200
And the response body is {"status": "ok"}
```

### Scenario 2: Backend CI job passes on clean push

```gherkin
Given a commit is pushed to main (or a PR is opened)
When the GitHub Actions backend job runs
Then Python 3.12 is set up
And pip install from requirements.txt succeeds
And ruff check exits 0
And pytest exits 0 with test_health passing
```

### Scenario 3: Frontend CI job passes on clean push

```gherkin
Given a commit is pushed to main (or a PR is opened)
When the GitHub Actions frontend job runs
Then node --check fanfest/frontend/assets/js/main.js exits 0
```

### Scenario 4: Linter catches a style violation

```gherkin
Given a developer pushes a commit that introduces a ruff lint error (e.g. unused import)
When the GitHub Actions backend job runs
Then ruff check exits non-zero
And the CI backend job is marked as failed
And no pytest run occurs (fail-fast)
```

### Scenario 5: Health endpoint is not a catch-all

```gherkin
Given the FastAPI backend is running
When I send GET /nonexistent
Then the response status is 404
And the health endpoint is not affected
```

## Technical Context

### Current State

- `fanfest/backend/app/main.py` — 1-line empty stub; no app object, no routes.
- `fanfest/backend/requirements.txt` — blank; no dependencies declared.
- `fanfest/backend/tests/` — directory exists with empty `__init__.py`; no test files.
- `.github/workflows/` — directory does not exist.
- `fanfest/frontend/assets/js/main.js` — 10.8 KB, exists and has content; suitable for `node --check`.

### Proposed Changes

| File | Action | Detail |
|------|--------|--------|
| `fanfest/backend/app/main.py` | Create | FastAPI app, CORS middleware, `GET /health` route inline (not in `api/v1/endpoints/` — intentional for infra-only scope) |
| `fanfest/backend/requirements.txt` | Create | `fastapi`, `uvicorn[standard]`, `pytest`, `httpx`, `ruff` with version pins |
| `fanfest/backend/tests/test_health.py` | Create | `TestClient` test asserting 200 + `{"status": "ok"}` |
| `.github/workflows/ci.yml` | Create | Two-job workflow: `backend` (Python 3.12, ruff, pytest) and `frontend` (node --check) |

### Constraints

- Python 3.12 only.
- Backend strictly infra: only `/health`. No product logic.
- Ruff line length follows code-conventions (88 chars — ruff default, no extra config needed).
- CI jobs must use `permissions: { contents: read }` (least privilege).
- Third-party actions (`actions/setup-python`, `actions/checkout`) pinned to major version or SHA.
- CORS must be configured in `main.py` because the frontend runs on a separate origin (port 8080) in local dev.

### Integration Points

- No external integrations for this ticket. Health endpoint is self-contained.
- `fanfest/frontend/assets/js/main.js` is read-only for CI (syntax check only, no modification).

### Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| `GET /health` inline in `main.py`, not under `api/v1/endpoints/` | Infra-only scope; convention says domain endpoints go in `api/v1/endpoints/`; health is not a domain feature |
| `ruff` as linter (not `flake8`, `pylint`) | Already in the draft spec; lightweight, fast, Python 3.12 compatible |
| `pytest` + `httpx` + FastAPI `TestClient` | Aligns with project testing-conventions |
| `node --check` for frontend CI | No bundler, no framework; syntax-only check is the appropriate minimal gate for vanilla JS |

### PYTHONPATH Note

Running `pytest` from `fanfest/backend/` requires Python to resolve `from app.main import app`. Add one of:
- `PYTHONPATH=.` in the CI step (`working-directory: fanfest/backend` + env `PYTHONPATH: .`), **or**
- A minimal `pyproject.toml` with `[tool.pytest.ini_options] pythonpath = ["."]` — preferred for reproducibility locally and in CI.

## Out Of Scope

- Any product endpoint (events, users, auth, recap, etc.) — arrives via product drafts + QAF.
- Database, ORM, or persistence layer.
- Frontend test framework (no framework decided yet; manual verification only per testing-conventions).
- Docker image or container CI job (infra-02).
- Production deploy or staging environment (infra-03).
- Google OAuth or Anthropic API integration tests.

## Future Considerations

- infra-02 will add Docker build step and image publish to CI.
- infra-03 will add deploy job (e.g. Pages, Fly.io, or similar).
- Once product endpoints exist, coverage thresholds can be added to the CI backend job.

## Edge Cases and Error Handling

| Case | Handling |
|------|----------|
| `GET /health` with unsupported `Accept` header | FastAPI returns 200; JSON is the only response format declared |
| `node --check` on a file with a syntax error | Node exits non-zero; frontend CI job fails; reported in PR checks |
| `requirements.txt` missing a declared dependency | `pip install` exits non-zero; CI backend job fails early (before ruff/pytest run) |
| pytest cannot import `app.main` (PYTHONPATH not set) | pytest exits with `ModuleNotFoundError`; blocked by PYTHONPATH fix above |

## Validation Rules

- `/health` must return exactly `{"status": "ok"}` — no extra fields.
- `ruff check` must exit 0 (no warnings, no errors).
- `pytest` must exit 0 (all tests pass, no collection errors).

## Dependencies

- **Blocking:** none — this ticket has no upstream blockers.
- **Enables:** infra-02 (Docker), infra-03 (deploy).

## Definition of Done

**Code quality**
- [ ] `ruff check fanfest/backend` exits 0 locally
- [ ] `pytest fanfest/backend` exits 0 locally
- [ ] `node --check fanfest/frontend/assets/js/main.js` exits 0 locally

**Testing**
- [ ] `tests/test_health.py` covers: 200 status + `{"status": "ok"}` body
- [ ] All 5 BDD scenarios are exercised (Scenarios 1 and 5 by unit test; Scenarios 2-4 by CI run)

**CI**
- [ ] `.github/workflows/ci.yml` passes on push to `main`
- [ ] Both `backend` and `frontend` jobs show green in the GitHub Actions tab
- [ ] Workflow has `permissions: { contents: read }` and all actions are pinned

**Review**
- [ ] PR reviewed and approved before merge to `main`

## Implementation Notes

- Run all commands from `fanfest/backend/` (per CLAUDE.md project instructions).
- Apply `sre-ai-toolkit:github-actions-secure-ci-cd-pipelines` skill when writing the workflow.
- Health route goes inline in `main.py` — deliberate exception to the `api/v1/endpoints/` convention for this infra-only ticket.
- CORS origin: allow `http://localhost:8080` for local development (frontend port).
- Do not add `Co-Authored-By` or any AI signature to commits (per global CLAUDE.md).

## References

- Draft: `specs/drafts/infra-01-ci-and-backend-health.md`
- Convention skills: `.claude/skills/code-conventions/SKILL.md`, `.claude/skills/testing-conventions/SKILL.md`
- SRE skill: `sre-ai-toolkit:github-actions-secure-ci-cd-pipelines`

## Wiki Evidence

- `docs/llm-wiki/wiki/services/backend.md` — confirms all backend files are empty stubs; requirements.txt blank; CORS needed in main.py; tests use FastAPI TestClient

## Graph Evidence

- No graph queries issued — wiki fully answered all structural questions. Impact radius is clearly bounded: 4 new/modified files, 1 service (backend), 0 cross-service dependencies.

---

**INVEST Validated**: ✅  
**BDD Scenarios**: 5  
**Priority**: High (unblocks infra-02 and infra-03)  
**Labels**: infra, ci, fastapi, github-actions  
**Scope impact**: ~4 files, 1 service, max_depth 2 (inferred — no graph query needed)
