# INFRA-04: Migrate Backend Persistence from In-Memory to SQLite

## User Story

**As a** FanFest developer  
**I want** all backend data (events, venues, registrations, photos, comments) stored in a SQLite database  
**So that** the app survives server restarts, data accumulates across sessions, and we can demo realistic behavior without reseeding on every boot.

---

## Stakeholders

- **Backend engineer** — implements ORM models, migrations, service layer changes
- **QA / demo owner** — needs data to persist across backend restarts for realistic demos
- **Frontend contributors** — no API contract changes; behavior is identical, only persistence improves

---

## Success Criteria

1. Backend starts with `uvicorn` and creates/migrates the SQLite DB automatically on first boot — no manual step.
2. All existing API endpoints (`/events`, `/checkin`, `/photos`, `/media`, `/recap`) return the same response shapes as today.
3. Seed data (events, venues, photos, comments) is loaded once on first boot; subsequent restarts reuse persisted data.
4. `pytest` passes with 0 failures; tests use an in-memory SQLite instance (not the dev DB file).
5. `ruff check` exits 0.

---

## Acceptance Criteria

### Scenario 1: Data survives a restart

```gherkin
Given a user checks in to an event and uploads a photo
When the backend process is restarted
Then the check-in and photo are still returned by the API
```

### Scenario 2: Seed data loads once

```gherkin
Given the database file does not exist
When uvicorn starts for the first time
Then events, venues, and seed photos are inserted
And on the next restart they are NOT re-inserted (no duplicates)
```

### Scenario 3: Media upload persists

```gherkin
Given a user uploads a photo via POST /{event_id}/media
When the backend is restarted
Then GET /{event_id}/media returns that photo
```

### Scenario 4: Like toggle persists

```gherkin
Given a user likes a photo
When the backend is restarted
Then the like count is preserved and liked_by_me is correct for that user
```

### Scenario 5: Tests use isolated in-memory DB

```gherkin
Given the test suite runs
When any test creates or modifies data
Then it uses an in-memory SQLite DB
And the dev DB file on disk is never touched
```

---

## Technical Context

### Current State

- All data lives in Python dicts/lists in `fanfest/backend/app/data/seed.py` and service modules.
- Every `uvicorn` restart wipes all state (registrations, uploaded photos, likes, comments).
- No ORM, no migration framework, no DB file.

### Proposed Stack

| Layer | Choice | Rationale |
|---|---|---|
| ORM | SQLAlchemy 2.x (async) | FastAPI-native async support; no extra abstraction needed |
| Migrations | Alembic | Standard for SQLAlchemy projects; auto-generates migration scripts |
| DB engine | SQLite (`fanfest.db`) | Zero-config, file-based, no server; perfect for demo/local |
| Test DB | `sqlite:///:memory:` | Isolated per test run; no cleanup needed |

### Proposed File Changes

| File | Action | Detail |
|---|---|---|
| `fanfest/backend/requirements.txt` | Update | Add `sqlalchemy>=2.0`, `alembic` |
| `fanfest/backend/app/db/base.py` | Create | `DeclarativeBase`, `async_engine`, `AsyncSession`, `get_db` dependency |
| `fanfest/backend/app/db/models.py` | Create | SQLAlchemy ORM models: `Event`, `Venue`, `Registration`, `Photo`, `Comment` |
| `fanfest/backend/alembic/` | Create | Alembic env + initial migration generating the schema |
| `fanfest/backend/app/data/seed.py` | Update | Seed runs inside a DB session; idempotent (check-before-insert) |
| `fanfest/backend/app/services/*.py` | Update | Replace dict lookups with `AsyncSession` queries |
| `fanfest/backend/app/main.py` | Update | Run `alembic upgrade head` on startup; inject DB session via dependency |
| `fanfest/backend/app/core/config.py` | Update | Add `database_url: str = "sqlite+aiosqlite:///./fanfest.db"` |
| `fanfest/backend/tests/conftest.py` | Create/Update | Override `get_db` dependency with in-memory SQLite session fixture |
| `.gitignore` | Update | Add `fanfest.db` |

### Constraints

- **No API contract changes** — all existing endpoint signatures, status codes, and response schemas stay identical.
- **No new endpoints** — pure persistence layer migration.
- **Existing dataclasses in `entities.py` stay** — used by tests and schemas; ORM models live separately in `db/models.py`.
- **Async all the way** — use `aiosqlite` driver + SQLAlchemy async session to stay compatible with FastAPI's async route handlers.
- **`MEDIA_STORAGE_BACKEND` env var logic unchanged** — media storage strategy is independent of DB engine.

### Architecture Decisions

| Decision | Rationale |
|---|---|
| Separate ORM models from Pydantic schemas | Keeps API contract stable; ORM is an implementation detail |
| Alembic over manual `CREATE TABLE` | Supports future schema evolution without manual SQL |
| `check-before-insert` seed strategy | Idempotent seed is safer than wiping DB on restart |
| `aiosqlite` driver | Required for SQLAlchemy async + SQLite; single extra dependency |

---

## Out Of Scope

- PostgreSQL or any other DB engine (future INFRA ticket).
- User authentication / sessions.
- Admin UI for DB management.
- Data export or backup tooling.

---

## Definition of Done

**Code quality**
- [ ] `ruff check fanfest/backend` exits 0 locally
- [ ] `pytest fanfest/backend` exits 0 locally (all existing + new tests pass)

**Persistence**
- [ ] Restarting uvicorn retains check-ins, photos, likes, comments
- [ ] Seed data is not duplicated on second boot

**Tests**
- [ ] All tests use in-memory SQLite (dev DB file not touched during test run)
- [ ] Scenarios 1–5 covered by automated tests

**Migration**
- [ ] `alembic upgrade head` runs automatically on startup
- [ ] `alembic` migration script exists and generates the correct schema

**Review**
- [ ] PR reviewed and approved before merge to `main`

---

## Dependencies

- **Requires:** FEST-08 merged (media endpoints must be in the service layer before migrating them to DB)
- **Enables:** future PostgreSQL migration (INFRA-05, if needed), multi-user sessions

---

**Priority:** High (unblocks realistic demo behavior)  
**Labels:** infra, backend, sqlite, sqlalchemy, alembic  
**Scope impact:** ~10 files, 1 service (backend), no frontend changes
