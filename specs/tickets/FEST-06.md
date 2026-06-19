# FEST-06: Recap Screen — Customizable AI Recap UI

## 📋 User Story

**As a** fan who has just finished watching a match at a fan fest
**I want** a polished, customizable recap screen that shows the final result, my prediction outcome, and the AI-generated match moments with my crew's photos
**So that** I can relive the event in my chosen tone and length and share the recap to social

---

## 👥 Stakeholders

| Role | Name | Responsibility |
|------|------|----------------|
| Requester | FanFest product team | Initial request, requirements validation |
| Product Owner | FanFest product team | Acceptance, prioritization |
| Tech Lead | FanFest engineering | Architecture review, technical approval |
| End Users | Fans (post-event / Recap mode) | Primary beneficiaries |

---

## 🎯 Success Criteria

1. The Recap screen renders all sections (Nav, Final-result slide, Prediction-stats slide, Match-moment slides, Customization panel) faithfully to the `Tribuna Recap.dc.html` design, reusing existing `assets/css/main.css` tokens.
2. The slides selector (3 / 5 / 8) changes the number of moment slides shown (2 / 3 / 5) and the tone selector recolors the screen accent across slide 2, moment markers, and CTAs.
3. The selected `tone` and `slideCount` are passed as inputs to the feature-04 recap generation so the AI narrative voice and number of moment slides reflect the user's choice.
4. `node --check` passes on the JS module and the page serves with no console errors using inline mock data.
5. **[Added]** The "Ver crónica" cards on the Home screen carry a `data-recap-event-id` attribute and are wired to navigate to the Recap screen inside the phone frame.
6. **[Added]** Before fetching the recap, the client validates that the entity exists and its match has ended (`status === 'ended'`); shows a graceful error otherwise.
7. **[Added]** The recap screen is rendered inside the `.phone` frame (hidden `#recapView` div), not outside it; navigation follows the same show/hide pattern as Event Detail.

**Metrics**: Visual parity with the design source on the four section groups; all 8 acceptance-criteria checkboxes from the draft pass on manual verification; zero console errors at load.

---

## ✅ Acceptance Criteria

### Scenario 1: Recap screen renders all sections faithfully (Happy Path)
```gherkin
Given the app is in post-event / Recap mode with inline mock data (final score, prediction stats, moments + photos)
And the Recap screen reuses the existing assets/css/main.css design tokens
When the Recap screen is shown
Then the Nav renders a back control labeled "Recap" and an overflow (dots) menu
And the Final-result slide shows both teams with flags, the final score "1 – 0", a "FINAL" label, and the competition, venue and date
And the Prediction-stats slide shows the two percentages ("68% de los fans acertó el resultado" and "68% predijo lo mismo que vos") and the user's pick "Argentina 1 – 0 México" with a confirmed check
And each Match-moment slide renders a labeled moment with its sub-line and a horizontal strip of portrait photo thumbnails tagged with the uploader's @handle
And the Customization panel renders the Slides count, Tone, and Share controls
```

### Scenario 2: Slides selector changes the number of moment slides (Behavior)
```gherkin
Given the Recap screen is displayed with the default slideCount
When the user selects "3" then "5" then "8" in the Slides selector
Then the number of visible moment slides updates to 2, then 3, then 5 respectively
And the selected slideCount is carried as the target length input to the feature-04 recap generation
```

### Scenario 3: Tone selector recolors the screen and drives the AI voice (Behavior)
```gherkin
Given the Recap screen is displayed with a default tone
When the user selects a tone among Emocionante / Inspirador / Humorístico / Nostálgico
Then the accent palette is recolored across the prediction-stats slide, the moment markers, and the CTAs
And the selected tone is passed to the feature-04 recap generation so the narrative voice matches the choice
```

### Scenario 4: Share row renders the full set of share targets (Happy Path)
```gherkin
Given the Recap screen is displayed
When the Customization panel's Share row is shown
Then it renders Instagram, WhatsApp, X, and copy-link controls
And it renders the primary "Compartir recap completo" CTA
```

### Scenario 5: Page serves cleanly with mock data (Quality Gate)
```gherkin
Given the Recap screen JavaScript module
When `node --check` is run against it
Then it exits with no syntax errors
And when the page is served and loaded in a browser there are no console errors
```

### Scenario 6: Recap generation unavailable — graceful fallback (Error Case)
```gherkin
Given the feature-04 recap generation is not yet wired or returns an error
When the Recap screen is shown
Then it renders the full layout from inline mock data without throwing
And the screen never blocks on a live feed (MVP has no live feeds)
```

### Scenario 7: Navigating to recap from Home — entity exists and match ended (Happy Path)
```gherkin
Given a recap card on the Home screen with data-recap-event-id="evt-006"
And the match for evt-006 exists in match_state with status "ended"
When the user taps "Ver crónica"
Then the home scroll hides and the recap screen shows inside the phone frame
And the AI recap is fetched and rendered for evt-006
```

### Scenario 8: Entity missing or match not ended — graceful gate (Error Case)
```gherkin
Given a recap card with data-recap-event-id="evt-999"
When the user taps "Ver crónica"
Then a user-friendly error message is shown ("Partido no disponible")
And the back button returns the user to the Home screen
```

---

## 🔧 Technical Context

### Current State
- Frontend is framework-free vanilla JS with no bundler: a single `fanfest/frontend/index.html`, `assets/css/main.css` (design tokens), `assets/js/main.js`, and an empty `assets/js/api.js`.
- `main.js` already renders a Home screen that includes a recap **card row** (`renderRecap()` / `recapCards`), but there is no full Recap **screen**.
- `main.css` exposes design tokens including `--accent`, `--accent-ink`, `--arg`, `--opp`, `--bg`, `--card`, `--ink`, `--muted`, `--screen`, `--label`, `--frame`, `--hair`, `--tag-bg`.
- The Home and Event Detail screens establish the data-driven vanilla-port approach this screen must mirror.

### Proposed Changes
- Port the Recap `.dc.html` design into the vanilla `fanfest/frontend` stack: replace the claude.ai/design runtime with plain data-driven HTML/CSS/JS, reusing `main.css` tokens.
- Add Recap markup to `fanfest/frontend/index.html`.
- Add Recap UI logic to `fanfest/frontend/assets/js/main.js` (or a new `recap.js` module), driven by inline mock data: final score, prediction stats, and moments with photo strips.
- Add any new styles to `fanfest/frontend/assets/css/main.css` (or a new `recap.css`), with no inline styles.
- Implement client state `slideCount` (3/5/8 → 2/3/5 visible moments) and `tone` (4 options), where tone maps to an accent palette applied across slide 2, moment markers, and CTAs.
- When wiring to the recap generation, route the call through `api.js` (single backend base URL there), passing `tone` and target length / `slideCount`.

### Technical Constraints
- Framework-free, no bundler — match the existing `fanfest/frontend` style.
- No inline styles; all CSS in `fanfest/frontend/assets/css/`.
- All browser API calls go through `api.js`; no scattered `fetch()` in `main.js`, and the backend base URL is defined only in `api.js`.
- JS file naming is `camelCase`; DOM IDs/classes are `kebab-case`.
- MVP uses inline mock data only — no live feeds.

### Integration Points
- **feature-04 (AI Recap)** — provides the AI narrative + labeled highlights; its `POST /api/v1/events/{id}/recap` endpoint must accept `tone` and a target length / slide count and reflect both in the narrative voice and number of moment slides. This screen supplies those two inputs.
- **feature-03 (Live event / Hype Wall)** — source of the per-moment photos and uploader `@handle`s shown in the moment photo strips.
- **feature-02 (Event details / RSVP / prediction)** — source of the prediction outcomes shown on the prediction-stats slide.

### Architecture Decisions
- **Vanilla data-driven port (no runtime framework)** — rationale: consistency with the Home and Event Detail screens and the framework-free `fanfest/frontend` constraint.
- **`tone` and `slideCount` are first-class client state and AI inputs** — rationale: this is the new capability over feature-04; tone changes both the visual accent and the AI narrative voice, length drives the number of moment slides.
- **Reuse `main.css` tokens, accent driven by tone** — rationale: keeps visual parity and avoids a parallel styling system.

---

## 🚫 Out of Scope

The following are explicitly NOT part of this ticket:
1. Implementing or modifying the feature-04 recap endpoint / Claude API call itself (this ticket consumes it and passes `tone` + length; the endpoint changes are owned by FEST-04).
2. Real share-to-social integration — share generates a shareable image/link, mocked for MVP (real only if time allows).
3. Live data feeds for score, prediction stats, moments, or photos — all mock data inline for MVP.

**Future Considerations**: Real shareable image/link generation; live data feeds; reactions and comments on the recap (covered by feature-04's broader social actions).

---

## ⚠️ Edge Cases & Error Handling

### Edge Cases
1. **Fewer real moments than the selected slide count**: render only the moments available; do not pad with empty slides.
2. **A moment has no photos**: render the moment label and sub-line, omit the photo strip (no broken thumbnails).
3. **Tone toggled repeatedly**: accent recolor is idempotent — re-applying a tone yields the same palette with no residual classes from the prior tone.

### Error Scenarios
1. **Recap generation (feature-04) fails or is not wired**: screen still renders the full layout from inline mock data and does not throw; the demo never breaks.
2. **A photo thumbnail fails to load**: the slide degrades gracefully (placeholder or omitted thumbnail) without a console error.

### Data Validation Rules
- `slideCount` must be one of {3, 5, 8}; map to {2, 3, 5} visible moments.
- `tone` must be one of {Emocionante, Inspirador, Humorístico, Nostálgico}; default to a single defined tone when unset.

---

## 📦 Dependencies

### Blocking
- [ ] FEST-04 (AI Recap) — its recap endpoint must accept `tone` + target length for the customization panel to drive generation. The UI can be built against mock data first, but full wiring depends on FEST-04.

### Related
- FEST-03 (Live event / Hype Wall) - supplies per-moment photos and uploader handles.
- FEST-02 (Event details / RSVP / prediction) - supplies prediction outcomes for the stats slide.

---

## 🎓 Definition of Done

### Code Quality
- [ ] All acceptance criteria scenarios implemented.
- [ ] Framework-free, no inline styles; all CSS under `fanfest/frontend/assets/css/`.
- [ ] All browser API calls routed through `api.js`; backend base URL defined only there.
- [ ] JS `camelCase`, DOM IDs/classes `kebab-case`.
- [ ] `node --check` passes on the recap JS module.

### Testing
- [ ] Manual verification of all six BDD scenarios (no frontend test framework is established per testing-conventions).
- [ ] Slides selector verified for 3/5/8 → 2/3/5 visible moments.
- [ ] Tone selector verified to recolor accent across slide 2, moment markers, and CTAs.
- [ ] Page serves with no console errors using inline mock data.
- [ ] Edge cases (missing photos, fewer moments than slide count, repeated tone toggles) verified manually.

### Documentation
- [ ] README updated if the recap screen surfaces new user-facing behavior.
- [ ] Any new prescriptive frontend rule added to the `code-conventions` skill.

### Review & Deployment
- [ ] Code reviewed and approved.
- [ ] PR merged to main.
- [ ] Deployed to the frontend host (port 8080) for stakeholder validation.
- [ ] Stakeholders validated visual parity with the design source.

---

## 🎨 UI Testing (if applicable)

### Test Levels
| Level | Required | Tool | Status |
|-------|----------|------|--------|
| Unit | No | — (no frontend test framework established) | - |
| Component | No | — | - |
| E2E | No | — | - |
| Visual | No (manual parity check vs design source) | Manual review | - |

### Figma Reference (if visual level)
- Design source: claude.ai/design → "Tribuna Fan Fests Discovery" → `Tribuna Recap.dc.html` (no Figma node; manual visual parity).

### Visual Testing Configuration (if visual level)
| Screen | Route | Figma Node | Viewport | Mode |
|--------|-------|------------|----------|------|
| Recap | Recap mode (post-event) | n/a | mobile | screenshot (manual) |

---

## 📝 Implementation Notes

- This is the hero / AI moment of the product — prioritize visual fidelity and the tone/length-aware path.
- Mirror the existing Home and Event Detail screen ports: data-driven HTML/CSS/JS, inline mock data, reuse `main.css` tokens.
- Mock data inline (final score, prediction stats, moments + photos) — same as the other screens, no live feeds in MVP.
- Tone maps to an accent palette applied across slide 2, moment markers, and CTAs, and also drives the AI narrative voice via the feature-04 generation inputs.
- Share = generate a shareable image/link; mock for MVP, real only if time allows.

### Gap-detection log
- Phase 0 preflight: exited 0; marker at `.claude-temp/tickets/feature-06-recap-screen/.preflight-ok` (graph fresh at HEAD).
- Phase 0.1: loaded `code-conventions`, `multi-file-workflows`, `testing-conventions`.
- Phase 0.2: `--skip-wiki` set — wiki preload bypassed; fell back to convention skills + CLAUDE.md and direct codebase inspection.
- Phase 2: all gaps resolved from the draft, convention skills, and the existing `fanfest/frontend` codebase + sibling drafts (feature-04, 03, 02). No engineer questions required.
- Phase 5a: impact-radius graph query skipped — single-screen, frontend-only slice with a bounded blast radius (`index.html` + `main.js`/`recap.js` + `main.css`); subjective "Small" evaluation applied.

---

## 🔗 References

- Draft: `specs/drafts/feature-06-recap-screen.md`
- Implements UI for: `specs/drafts/feature-04-ai-recap.md`
- Design source: claude.ai/design → "Tribuna Fan Fests Discovery" → `Tribuna Recap.dc.html`
- Convention skills: `.claude/skills/code-conventions/SKILL.md`, `.claude/skills/multi-file-workflows/SKILL.md`, `.claude/skills/testing-conventions/SKILL.md`

---

**Created**: 2026-06-19
**Created By**: Claude (create-sdd-ticket skill)
**INVEST Validated**: ✅
**BDD Scenarios**: 6
**Priority**: Medium
**Labels**: sdd, frontend, recap, ai, ui
