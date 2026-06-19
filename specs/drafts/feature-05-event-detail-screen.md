# Feature 05 — Event Detail Screen (Previa)

**Flow steps:** 3–6 (event info → predict → check-in → live hype feed) · **Risk hint:** MEDIUM · **Strategy:** PLAN_FIRST
**AI in product:** none (screen UI; consumes the feature-02 / feature-03 backends) · **Slice:** UI
**Design source:** claude.ai/design → "Tribuna Fan Fests Discovery" → `Tribuna Event Detail.dc.html`
**Implements UI for:** [`feature-02-event-details-rsvp`](./feature-02-event-details-rsvp.md) (detail, prediction, check-in) + [`feature-03-live-event-hype-wall`](./feature-03-live-event-hype-wall.md) (hype feed, photo/video upload). Reached from a Home card (feature-01).

## Description

Vanilla port of the Event Detail `.dc.html` into `fanfest/frontend`, same approach
as the Tribuna Home screen: replace the claude.ai/design runtime (`sc-for`/`sc-if`/
`DCLogic`/`support.js`) with plain data-driven HTML/CSS/JS, reusing the design
tokens already in `assets/css/main.css`. This is the pre-match ("Previa") state of
a fan fest.

**Sections (top → bottom):**
- **Back row** — arrow + venue name; returns to Home.
- **Match header** — both teams (flag avatar + name), empty score placeholder (`– : –`), a glowing **PREVIA** status pill, an animated countdown ("Comienza en 10 min"), and a competition label ("FIFA World Cup 2026 · Grupo C · Jornada 2").
- **Event info** — venue + distance, "47 van" attendees pill, horizontally scrolling amenity chips.
- **Action buttons** — "Subir foto" (disabled until the match starts) and "Predecir" (toggles the prediction panel).
- **Prediction panel** (inline, toggled) — ARG/MEX score steppers (`+`/`–`, clamp 0–9) and "Confirmar predicción →"; on submit, collapses to a confirmed state ("Predicción enviada · Argentina X – Y México").
- **Hype feed** ("Previa" divider) — user posts: avatar, `@handle`, time-ago, optional photo/video placeholder (with duration badge), caption, and react/comment/share actions (some posts show like + comment counts).
- **Empty state** — "Los eventos del partido aparecerán aquí · Inicio · Goles · Entretiempo · Fin".
- **Floating action button** — fixed "Subir foto / video" CTA over a gradient.

**State / interactions (from the design):**
- `showPredict` toggle, `homeScore`/`awayScore` steppers (clamped 0–9), `submitPredict` → `predictSent` confirmed state.
- "Subir foto" action button disabled in the Previa state.

## Acceptance Criteria

- [ ] Event Detail screen renders all sections faithfully to the design, reusing existing CSS tokens.
- [ ] Tapping a Home event card navigates to this screen for that event.
- [ ] "Predecir" toggles the prediction panel; steppers adjust ARG/MEX scores (clamped 0–9).
- [ ] "Confirmar predicción" collapses the panel into the confirmed state showing the chosen scoreline.
- [ ] "Subir foto" is disabled before kickoff; the floating "Subir foto / video" CTA is visible.
- [ ] Hype feed renders posts (photo, video, and text variants) with react/comment/share actions.
- [ ] Empty state shows when there are no match events yet.
- [ ] `node --check` passes; page serves with no console errors (mock data inline).

## Notes

- Mock data inline (match, venue, amenities, feed posts), same as the Home screen — no live feeds in MVP.
- Wire the prediction panel to feature-02's `POST /events/{id}/predictions` and the upload CTA to feature-03's photo endpoint once those backends exist; until then, mock the calls.
- Apply QAF skills: front-end conventions in `code-conventions`; keep it framework-free to match the existing `fanfest/frontend`.
