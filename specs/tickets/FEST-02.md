# FEST-02: Event Detail, Invite, Prediction & Check-in

## 📋 User Story

**As a** registered FanFest fan attending a match watch-party
**I want** to view an event's full details, invite friends, predict the result, save the event to my calendar, navigate to the venue, see who else is attending, and check in when I arrive
**So that** I can prepare for the match, bring my friends, commit a prediction for the recap, and unlock the live in-venue experience.

---

## 👥 Stakeholders

| Role | Name | Responsibility |
|------|------|----------------|
| Requester | Product (FanFest) | Initial request, requirements validation |
| Product Owner | FanFest PO | Acceptance, prioritization |
| Tech Lead | Backend/Full-stack lead | Architecture review, technical approval |
| End Users | FanFest fans (attendees) | Primary beneficiaries |

---

## 🎯 Success Criteria

1. A fan can open an event and see complete detail (teams, venue, time, organizer, attendee list) sourced from `GET /api/v1/events/{id}`.
2. A fan can submit a result prediction once per event, persisted to their identity, and is blocked from changing it after the (mocked) match-start time.
3. A fan can check in via "Ya estoy acá", which marks them present and routes to the live screen (Feature 03).
4. A fan can share/invite by link, add the event to Google Calendar, and open Google Maps directions to the venue.
5. A lightweight, persistent registered user identity exists so predictions (and later photo uploads) attribute to a user.

**Metrics**: All eight draft acceptance criteria pass; all BDD scenarios have automated backend tests; the frontend event-detail view performs a successful prediction + check-in round-trip against the running backend.

---

## ✅ Acceptance Criteria

### Scenario 1: Happy Path — view detail, predict, and check in
```gherkin
Given a registered user with a persistent identity
And an event exists with teams, venue, time, organizer, and attendees
When the user opens the event detail view
Then GET /api/v1/events/{id} returns the full event detail including the attendee list and a shareable invite link
When the user submits a result prediction before match start
Then POST /api/v1/events/{id}/predictions persists the prediction for that user and returns it
When the user taps "Ya estoy acá"
Then POST /api/v1/events/{id}/checkin marks the user present
And the frontend routes to the live screen (Feature 03)
```

### Scenario 2: Edge Case — prediction is locked after match start
```gherkin
Given a registered user who has submitted a prediction for an event
And the event's mocked match-start time has passed
When the user attempts to change their prediction via POST /api/v1/events/{id}/predictions
Then the request is rejected with HTTP 409 and detail "Predictions are closed (match has started)"
And the originally stored prediction is unchanged
```

### Scenario 3: Edge Case — first prediction submitted, then re-submitted before match start
```gherkin
Given a registered user who has already submitted a prediction for an event
And the event has not yet started
When the user submits a new prediction via POST /api/v1/events/{id}/predictions
Then the stored prediction for that user is overwritten with the new value
And exactly one prediction remains stored for that user and event
```

### Scenario 4: Error Case — event not found
```gherkin
Given no event exists with id 9999
When the user requests GET /api/v1/events/9999 (or posts a prediction/check-in to it)
Then the API responds with HTTP 404 and detail "Event not found"
```

### Scenario 5: Error Case — check-in without a known user identity
```gherkin
Given a check-in request that carries no resolvable user identity
When the user calls POST /api/v1/events/{id}/checkin
Then the API responds with HTTP 400 and detail "User identity required"
And no attendance record is created
```

---

## 🔧 Technical Context

### Current State
- Greenfield backend: `fanfest/backend/app/main.py`, `requirements.txt`, and all endpoint modules are empty stubs (Infra-01 introduces only `GET /health`).
- No `events.py` endpoint, no predictions/check-in logic, no persistence layer, and no user-identity model exist yet.
- Frontend (`fanfest/frontend`, vanilla JS, no bundler) does not yet have the event-detail view wired to a backend; Feature 05 ports the detail screen UI and currently mocks these calls.

### Proposed Changes
- **Backend endpoints** in `fanfest/backend/app/api/v1/endpoints/events.py`:
  - `GET /api/v1/events/{event_id}` — full event detail (teams, venue, time, organizer, attendees, invite link).
  - `POST /api/v1/events/{event_id}/predictions` — persist a per-user result prediction; reject changes after match start.
  - `POST /api/v1/events/{event_id}/checkin` — mark the user present.
  - Register the router in `fanfest/backend/app/main.py` via `app.include_router(...)` (router only takes effect when included).
- **Service layer** `fanfest/backend/app/services/predictions_service.py` — prediction validation (match-start lock) and storage; check-in/attendance handling may live alongside or in a peer service.
- **Schemas** (Pydantic) for event detail, prediction request/response, and check-in — defined alongside the endpoint or in `fanfest/backend/app/schemas/`.
- **Lightweight user identity** — a persistent registered-user concept (`name` + `id`) so predictions and (future) uploads attribute to a user; stored in the same persistence store as events/predictions.
- **Frontend wiring** — the event-detail view + prediction widget (delivered by Feature 05) call `api.js` functions for detail, prediction, and check-in; the backend base URL stays defined only in `api.js`.

### Technical Constraints
- Python backend on FastAPI; PEP 8, line length 88; raise `HTTPException` for 4xx, never encode error state in a 200 body.
- New dependencies must be pinned in `fanfest/backend/requirements.txt` before import.
- Match-start time is **mocked** (no live third-party feed); the prediction lock is evaluated against this mocked time.
- Prediction model kept simple for the demo: a scoreline (home/away integers, clamped 0–9 to match the Feature 05 steppers) or equivalently home/away/draw.
- All browser API calls go through `fanfest/frontend/assets/js/api.js` only.

### Integration Points
- **Feature 05 (Event Detail screen UI)** consumes these endpoints (detail render, prediction submit, check-in CTA).
- **Feature 03 (Live event)** is the route target after a successful check-in; it also relies on the same persistent user identity for photo attribution.
- **Feature 04 (AI recap)** reads stored predictions to reveal them in the recap.
- **Google Calendar** (calendar link/event generation) and **Google Maps** (venue directions link) — produced as working links from event data; deep Google OAuth integration is not required for these link-outs in the MVP.

### Architecture Decisions
- **Decision**: Use a simple in-process/persistent store (e.g. an in-memory store seeded with mock event data, optionally backed by a small SQLite/JSON file) for events, users, predictions, and attendance. **Rationale**: The drafts describe an MVP/demo with mocked match state and inline mock data across features; a heavyweight database is not warranted. Identity and predictions only need to be persistent within a running session, "keep it simple for the demo." (See Open Question 1 if the team requires durable cross-restart storage.)
- **Decision**: Prediction stored per `(user_id, event_id)` with overwrite-before-start semantics and a hard lock at the mocked match-start time. **Rationale**: Matches "cannot change their prediction after match start" while allowing pre-start corrections that the Feature 05 stepper UI implies.
- **Decision**: Calendar and Maps are produced as standard link-outs (Google Calendar template URL, Google Maps directions URL) built from event fields. **Rationale**: Resident-Advisor-style takeaway achievable without OAuth; avoids scope creep into Google auth for this ticket.

---

## 🚫 Out of Scope

The following are explicitly NOT part of this ticket:
1. The event-detail **screen UI** itself and its visual fidelity — owned by Feature 05 (this ticket delivers the backend it consumes plus the API-client wiring).
2. The **live event screen and Hype Wall** (photo/video upload, live gallery) — owned by Feature 03.
3. The **AI recap** that reveals predictions — owned by Feature 04.
4. Full **Google OAuth** sign-in / authenticated Calendar event creation; only link-out URLs are produced here.
5. **Event discovery / listing** (the Home feed) — owned by Feature 01.

**Future Considerations**: Durable cross-restart persistence (a real database), authenticated Google Calendar event insertion, and richer prediction models (per-scorer, exact-minute) may be addressed later.

---

## ⚠️ Edge Cases & Error Handling

### Edge Cases
1. **Re-submitting a prediction before match start**: overwrite the existing prediction; keep exactly one per user/event.
2. **Prediction attempted after the mocked match-start time**: reject with 409; stored value unchanged.
3. **Duplicate check-in by the same user**: idempotent — the user stays "present"; no error, no duplicate attendance record.
4. **Scoreline bounds**: home/away scores clamped to 0–9 (mirrors the Feature 05 steppers); out-of-range values are rejected by validation.

### Error Scenarios
1. **Event not found** (detail, prediction, or check-in on an unknown id): HTTP 404, detail "Event not found".
2. **No resolvable user identity on a prediction or check-in**: HTTP 400, detail "User identity required"; no record created.
3. **Invalid prediction payload** (missing/non-integer scores, out of range): HTTP 422 (FastAPI validation) or 400 with a clear message; nothing persisted.

### Data Validation Rules
- `event_id` must reference an existing event.
- Prediction requires a user identity and a valid scoreline (home/away integers 0–9) or a valid home/away/draw outcome.
- A user has at most one stored prediction per event.
- Predictions are mutable only strictly before the mocked match-start time.

---

## 📦 Dependencies

### Blocking
- [ ] INFRA-01 — minimal FastAPI app + CI green (provides the app entry point and pipeline these endpoints attach to).

### Related
- Feature 05 (Event Detail screen UI) — consumes these endpoints; provides the prediction widget and check-in CTA.
- Feature 03 (Live event / Hype Wall) — route target after check-in; shares the persistent user identity.
- Feature 04 (AI recap) — reads stored predictions.
- Feature 01 (Event discovery) — navigates into this event from a Home card.

---

## 🎓 Definition of Done

### Code Quality
- [ ] All acceptance criteria scenarios implemented
- [ ] Unit test coverage ≥ 80% on new backend logic
- [ ] Integration test coverage = 100% (all BDD scenarios)
- [ ] `ruff check` passes with zero warnings
- [ ] Type checking passes (Pydantic models typed)
- [ ] Code formatted per project standards (Black/PEP 8, line length 88; isort import order)

### Testing
- [ ] All BDD scenarios have corresponding automated tests in `fanfest/backend/tests/test_events.py` using FastAPI `TestClient`
- [ ] Prediction-lock (post-match-start) and overwrite-before-start paths tested
- [ ] 404 (event not found) and 400 (missing identity) error handling tested
- [ ] Frontend prediction + check-in round-trip manually verified against the running backend (no frontend test framework established)

### Documentation
- [ ] New `/api/v1/events/*` endpoints documented (FastAPI auto-docs + brief notes)
- [ ] README updated if user-facing behavior changes
- [ ] Prescriptive rules added to the relevant convention skill (`code-conventions`, `multi-file-workflows`, or `testing-conventions`); descriptive context flows to `docs/llm-wiki/` via `/wiki-refresh`

### Review & Deployment
- [ ] Code reviewed and approved
- [ ] PR merged to main
- [ ] Deployed to staging
- [ ] Stakeholders validated implementation

---

## 📝 Implementation Notes

- Suggested files (from the draft): `fanfest/backend/app/api/v1/endpoints/events.py` (detail, predictions, checkin), `fanfest/backend/app/services/predictions_service.py`, and the frontend event-detail view + prediction widget (Feature 05).
- Follow the **Adding a New API Endpoint** checklist (`multi-file-workflows`): create the endpoint module, **register the router in `main.py`** (router has no effect unless included), declare Pydantic models, add `test_events.py`.
- Follow the **Adding a New Frontend Feature** checklist for the API-client wiring: add fetch functions to `api.js` (base URL defined only there), keep logic in `main.js`/feature module, no scattered `fetch()` calls.
- Keep the user identity lightweight (`name` + `id`) but persistent across the session so predictions and later uploads attribute correctly.
- Mock the match-start time so the prediction lock is testable deterministically.

## 🔗 References

- Draft: `specs/drafts/feature-02-event-details-rsvp.md`
- Related drafts: `specs/drafts/feature-05-event-detail-screen.md`, `specs/drafts/feature-03-live-event-hype-wall.md`, `specs/drafts/feature-04-ai-recap.md`, `specs/drafts/infra-01-ci-and-backend-health.md`
- Conventions: `.claude/skills/code-conventions/SKILL.md`, `.claude/skills/multi-file-workflows/SKILL.md`, `.claude/skills/testing-conventions/SKILL.md`, `.claude/CLAUDE.md`

## 📊 Wiki Evidence

- Skipped — `--skip-wiki` was passed; Phase 0.2 wiki/graph preload bypassed. Fell back to convention skills + `.claude/CLAUDE.md`.

## 📊 Graph Evidence

- Phase 5a impact-radius check skipped: target files (`events.py`, `predictions_service.py`) do not yet exist in the greenfield backend, so no concrete `changed_files` could be supplied to `mcp__code_graph__get_impact_radius_tool`. Subjective scope: single backend service + one frontend wiring touch — within "Small."

---

## INVEST Validation

- **Independent**: ✅ — depends only on INFRA-01 (app entry + CI), which is already a separate prerequisite ticket.
- **Negotiable**: ✅ — persistence mechanism and prediction-model shape are left as architecture decisions / open questions.
- **Valuable**: ✅ — delivers the core pre-match fan flow (detail, invite, predict, check-in).
- **Estimable**: ✅ — bounded set of three endpoints + a service + frontend wiring on a greenfield backend.
- **Small**: ✅ — single backend service, ~1–3 days; no cross-service blast radius (graph check not applicable on greenfield, subjective scope is small).
- **Testable**: ✅ — every scenario maps to a `TestClient` test; prediction lock is deterministic via the mocked match-start time.

## Assumptions & Open Questions

1. **Persistence durability**: assumed an in-process persistent store is acceptable for the demo (consistent with mocked match state and inline mock data across features). Confirm if durable cross-restart storage (e.g. SQLite/JSON file) is required.
2. **Identity provisioning**: assumed the lightweight user identity (`name` + `id`) is created/resolved by a simple registration or first-use mechanism shared across features; this ticket assumes the identity is available on the request. Confirm how the `id` is supplied to the prediction/check-in calls (header, body, or session).

---

**Created**: 2026-06-19
**Created By**: Claude (create-sdd-ticket skill)
**Source**: markdown (`specs/drafts/feature-02-event-details-rsvp.md`)
**INVEST Validated**: ✅
**BDD Scenarios**: 5
**Priority**: Medium
**Labels**: sdd, backend, frontend, events, predictions, checkin
