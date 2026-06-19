# FEST-04: AI-Generated Event Recap (Hero Feature)

## User Story

**As a** FanFest attendee whose match has just ended
**I want** the app to generate a personalized AI narrative recap of the event, reveal who predicted the score correctly, and display a photo carousel from the Hype Wall
**So that** I relive the fan fest experience, celebrate accurate predictions, and have a shareable memory of the event — while the product demonstrates a visible, explainable AI moment the jury can evaluate.

---

## Stakeholders

| Role | Name | Responsibility |
|------|------|----------------|
| Product Owner | FanFest PO | Acceptance, prioritization |
| Tech Lead | Backend/Full-stack lead | Architecture review, technical approval |
| AI Lead | FanFest AI reviewer | Prompt quality and explainability review |
| End Users | FanFest fans (attendees) | Primary beneficiaries |

---

## Success Criteria

1. `POST /api/v1/events/{id}/recap` calls the Claude API with structured event context (venue, date, attendees, final score, goals list, photo count) and returns a narrative recap with labeled highlights.
2. The recap response includes at least the highlights list and the narrative text; both vary according to the `tone` and `slide_count` parameters supplied by the caller.
3. If the Anthropic API call fails (network error, quota, timeout), the endpoint returns a graceful fallback response (templated summary) with HTTP 200 — the demo never surfaces a 500 to the frontend.
4. The frontend recap view shows: final score, correct-prediction reveal, AI narrative wrap-up, photo carousel, social actions (share/react/comment), and next-event suggestions.
5. A loading state ("Analizando la vibra del evento...") is displayed while the recap generates.

**Metrics**: All BDD scenarios have automated backend tests; the Anthropic client is mocked in tests; the live demo path succeeds end-to-end with a real `ANTHROPIC_API_KEY` in `.env`.

---

## Acceptance Criteria

### Scenario 1: Happy Path — recap generated successfully

```gherkin
Given a match for event_001 has ended (status: "ended")
And ANTHROPIC_API_KEY is set in the environment
And the event has 3 goals and 5 uploaded photos
When the fan calls POST /api/v1/events/event_001/recap with tone "emocionante" and slide_count 4
Then the API returns HTTP 200
And the response contains a "highlights" list with at least one labeled moment
And the response contains a "narrative" string with a personalized, emotional-tone recap
And the number of highlights does not exceed slide_count
```

### Scenario 2: Edge Case — AI call fails, fallback returned

```gherkin
Given a match for event_001 has ended
And the Anthropic API call raises a network exception
When the fan calls POST /api/v1/events/event_001/recap
Then the API returns HTTP 200
And the response contains a "highlights" list with at least one templated entry
And the response contains a "narrative" string with a generic fallback summary
And the response body includes "fallback": true
```

### Scenario 3: Error Case — recap requested before match ends

```gherkin
Given the match for event_001 has status "live" or "pre"
When the fan calls POST /api/v1/events/event_001/recap
Then the API returns HTTP 409
And the detail message is "Recap is only available after the match ends"
```

### Scenario 4: Error Case — event not found

```gherkin
Given no event exists with id "no_such_event"
When the fan calls POST /api/v1/events/no_such_event/recap
Then the API returns HTTP 404
And the detail message is "Event not found"
```

### Scenario 5: Happy Path — tone and slide_count shape the narrative

```gherkin
Given a match for event_001 has ended
And ANTHROPIC_API_KEY is set
When the fan calls POST /api/v1/events/event_001/recap with tone "humorístico" and slide_count 2
Then the narrative adopts a humorous voice (verified by acceptance test with mocked response)
And the highlights list contains at most 2 entries
```

### Scenario 6: Happy Path — prediction reveal in recap

```gherkin
Given the match for event_001 has ended with home_score 2, away_score 1
And user_001 predicted "2-1" (correct) and user_002 predicted "1-0" (wrong)
When the fan calls GET /api/v1/events/event_001/recap (or the data is embedded in POST response)
Then the recap response includes correct_predictors: ["user_001"]
```

### Scenario 7: Frontend — loading state during generation

```gherkin
Given the frontend triggers a recap request
And the API response takes more than 500 ms
When the recap screen mounts
Then the UI shows the loading message "Analizando la vibra del evento..."
And the main recap content is hidden until the response arrives
```

---

## Technical Context

### Current State

- `fanfest/backend/app/api/v1/endpoints/events.py` — 4 routes: match-state (GET/POST), photos (POST/GET). No recap route.
- `fanfest/backend/app/services/` — `match_state.py`, `photos_service.py`, `registry.py`. No `recap_service.py`.
- `fanfest/backend/app/schemas/events.py` — `MatchState`, `Photo`, `PhotoList`, `MatchStateUpdate`. No recap schemas.
- `fanfest/backend/app/core/config.py` — `Settings` has CORS, Drive config. No `ANTHROPIC_API_KEY` field.
- `fanfest/backend/requirements.txt` — does NOT contain `anthropic`. Must be added before importing.
- `fanfest/frontend/assets/js/api.js` — 4 functions. No recap call.
- No frontend recap view (`recap.js`, `recap.css`) exists.

### Proposed Changes

1. **`fanfest/backend/requirements.txt`** — add `anthropic>=0.25.0`.
2. **`fanfest/backend/app/core/config.py`** — add `anthropic_api_key: str = ""` to `Settings`.
3. **`fanfest/backend/app/schemas/events.py`** — add `RecapRequest`, `RecapHighlight`, `RecapResponse` Pydantic models.
4. **`fanfest/backend/app/services/recap_service.py`** (new) — `generate_recap(event_id, state, photos, tone, slide_count) -> RecapResponse`. Calls Anthropic `messages.create`; wraps exception in fallback response.
5. **`fanfest/backend/app/api/v1/endpoints/events.py`** — add `POST /{event_id}/recap` handler (`create_recap`). Returns 409 if match not ended.
6. **`fanfest/backend/tests/test_events.py`** (or new `test_recap.py`) — tests for recap endpoint; mock `anthropic.Anthropic` client.
7. **`fanfest/frontend/assets/js/api.js`** — add `fetchRecap(eventId, tone, slideCount)` function.
8. **`fanfest/frontend/assets/js/recap.js`** (new) — recap screen logic: loading state, narrative render, photo carousel, correct-prediction reveal, share/react/comment actions, next-event suggestions.
9. **`fanfest/frontend/assets/css/recap.css`** (new) — styles for recap view.
10. **`fanfest/frontend/index.html`** — add recap screen section and link to `recap.js` / `recap.css`.

### Technical Constraints

- `anthropic` must be declared in `requirements.txt` before importing (CI installs from that file; missing entry fails in GitHub Actions even if locally installed).
- All API calls from the browser go through `api.js` — no `fetch()` calls scattered in `recap.js`.
- Anthropic client must be mocked in tests to avoid billing and flakiness.
- Fallback response must return HTTP 200 (not 500) so the demo never breaks.
- `ANTHROPIC_API_KEY` is gated via `Settings`; the service should check for an empty key and raise a clear error or fall back immediately rather than letting the Anthropic SDK surface a 401 mid-demo.

### Integration Points

- **Anthropic API** — `POST /v1/messages` via `anthropic.Anthropic(api_key=...)`. Model: `claude-sonnet-4-6` or latest available.
- **match_state service** — read `status`, `goals`, `home_score`, `away_score`, `venue` to build the prompt context.
- **photos_service** — read photo count / metadata to enrich the recap narrative.
- **Feature 02 predictions** — read who predicted correctly for the prediction-reveal section. (Feature 02 not yet implemented; recap endpoint should return `correct_predictors: []` when prediction data is unavailable, rather than failing.)

### Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| `recap_service.py` as a standalone service module | Follows existing layered pattern (`match_state.py`, `photos_service.py`); isolates Anthropic client instantiation and prompt construction |
| Fallback to templated summary on AI failure, HTTP 200 | Demo resilience is a hard requirement; a 500 on stage is worse than a generic text |
| `tone` and `slide_count` as request body fields (not query params) | Consistent with `MatchStateUpdate` pattern; allows future extension without URL changes |
| Predictions data returns `[]` when Feature 02 is absent | Avoids hard dependency on unimplemented feature; ticket stays independent |
| Model selection via config, not hardcoded | Allows swapping `claude-sonnet-4-6` for `claude-opus-4-8` or newer models without code changes |

---

## Out Of Scope

- Recap customization panel UI (driven by `feature-06-recap-screen`; that ticket covers the UI controls for tone/slide selection).
- Persistent storage of generated recaps across server restarts (in-memory only, consistent with existing data layer).
- Real prediction data integration (Feature 02); this ticket returns `correct_predictors: []` when unavailable.
- Authentication / user sessions (no auth layer exists).
- Social share deep integration (share action opens native share API or copies a URL; no backend posting to social networks).

---

## Edge Cases and Error Handling

| Case | Handling |
|------|----------|
| Match not ended (status "pre" or "live") | HTTP 409, detail: "Recap is only available after the match ends" |
| Event not found | HTTP 404 (delegated to `match_state_service.get_state`) |
| Anthropic API error (network, quota, 4xx/5xx) | Catch all exceptions; return `RecapResponse` with `fallback=True` and templated text |
| Empty `ANTHROPIC_API_KEY` | Return fallback immediately without attempting API call |
| `tone` not one of the four valid values | HTTP 422 via Pydantic validation on `RecapRequest` |
| `slide_count` out of range (< 1 or > 10) | HTTP 422 via Pydantic `Field(ge=1, le=10)` |
| Photo list empty | Generate recap from match data only; narrative notes no photos were uploaded |
| Recap called multiple times for same event | Allowed; each call generates a fresh recap (no caching) |

### Validation Rules

- `tone`: `Literal["emocionante", "inspirador", "humorístico", "nostálgico"]`
- `slide_count`: `int`, 1–10, default 4
- `event_id`: must resolve to an existing event in `match_state_service`

---

## Dependencies

- **Blocking**: None — this ticket is self-contained given the fallback for missing prediction data.
- **Related**:
  - FEST-02 (prediction data for correct-predictor reveal — returns `[]` if absent)
  - FEST-03 (Hype Wall photos used in carousel and recap context)
  - FEST-06 (Recap Screen customization panel that surfaces `tone`/`slide_count` controls to the user)

---

## Definition Of Done

### Code Quality

- [ ] `ruff check .` passes with no errors (run from `fanfest/backend/`)
- [ ] `anthropic>=0.25.0` added to `fanfest/backend/requirements.txt`
- [ ] `ANTHROPIC_API_KEY` surfaced in `Settings` (pydantic-settings, loaded from `.env`)
- [ ] All new functions follow verb-prefix naming convention (`create_recap`, `generate_recap`)
- [ ] `HTTPException` used for all error responses; no bare `except` returning an error dict

### Testing

- [ ] `test_create_recap_returns_narrative` — mocked Anthropic client, match ended, asserts 200 + highlights + narrative
- [ ] `test_create_recap_fallback_on_ai_failure` — Anthropic raises exception, asserts 200 + `fallback: true`
- [ ] `test_create_recap_before_match_ends_returns_409` — match status "live", asserts 409
- [ ] `test_create_recap_unknown_event_returns_404` — unknown event_id, asserts 404
- [ ] `test_create_recap_invalid_tone_returns_422` — tone "invalid", asserts 422
- [ ] Anthropic mock added to `conftest.py` reset fixture or inline in test module

### Documentation

- [ ] Prompt construction documented in `README.md` under "How AI Was Used" section
- [ ] OpenAPI `/docs` reflects the new endpoint (automatic via FastAPI)

### Review and Deployment

- [ ] Code reviewed and approved by Tech Lead
- [ ] CI (`pytest` + `ruff`) passes on GitHub Actions
- [ ] Live demo path tested end-to-end with a real `ANTHROPIC_API_KEY`
- [ ] Fallback path verified by temporarily unsetting `ANTHROPIC_API_KEY`

---

## Wiki Evidence

- `docs/llm-wiki/wiki/services/backend.md` — confirms existing route table, service layer pattern, ANTHROPIC_API_KEY config, requirements.txt dependency rule, and test conventions

## Graph Evidence

- Tool: `mcp__code_graph__get_impact_radius_tool` — params: `{"changed_files": ["fanfest/backend/app/services/recap_service.py", "fanfest/backend/app/api/v1/endpoints/events.py", "fanfest/backend/app/schemas/events.py", "fanfest/backend/app/core/config.py"], "max_depth": 2, "detail_level": "minimal"}` — finding: 8 additional files affected, 1 service, 32 nodes within 2 hops — INVEST "Small" passes

---

## Implementation Notes

The Anthropic prompt should be structured and explainable — feed event context as a JSON block, then ask for (a) a `highlights` list of labeled moment objects and (b) a `narrative` string. Keeping the prompt structured (rather than freeform) makes the AI usage visible and auditable, which directly scores the "AI is visible and explainable" criterion.

Suggested prompt skeleton for `recap_service.py`:

```
You are a sports event narrator. Given the following fan fest context, return a JSON object with two keys:
- "highlights": an array of {"label": "...", "description": "..."} objects (at most {slide_count})
- "narrative": a short {tone} recap paragraph in Spanish

Context:
{structured_event_json}
```

The Anthropic client should be instantiated once at module level and accept the key from `settings.anthropic_api_key`, following the same pattern used by `photos_service.py` for the Google API client.

---

## References

- Draft spec: `specs/drafts/feature-04-ai-recap.md`
- Existing endpoint module: `fanfest/backend/app/api/v1/endpoints/events.py`
- Existing service pattern: `fanfest/backend/app/services/photos_service.py`
- Recap customization panel: `specs/drafts/feature-06-recap-screen.md`
- Anthropic Python SDK: `https://github.com/anthropic/anthropic-sdk-python`

---

**INVEST Validated**: Yes
**BDD Scenarios**: 7
**Priority**: High
**Labels**: sdd, ai-feature, hero-feature, anthropic
**Scope Impact**: impacted_services=1, impacted_files=8, max_depth=2 (tool: `mcp__code_graph__get_impact_radius_tool`)
