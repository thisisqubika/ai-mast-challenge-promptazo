# Feature 06 — Recap Screen (AI Recap UI)

**Flow steps:** 7–10 (post-event recap) · **Risk hint:** MEDIUM · **Strategy:** PLAN_FIRST
**AI in product:** YES — renders and triggers the feature-04 recap generation · **Slice:** UI (+ AI params)
**Design source:** claude.ai/design → "Tribuna Fan Fests Discovery" → `Tribuna Recap.dc.html`
**Implements UI for:** [`feature-04-ai-recap`](./feature-04-ai-recap.md). Reached after match end (post-event / Recap mode).

## Description

Vanilla port of the Recap `.dc.html` into `fanfest/frontend`, same approach as the
Home and Event Detail screens (replace the claude.ai/design runtime with plain
data-driven HTML/CSS/JS, reuse `assets/css/main.css` tokens). This is the hero /
AI moment of the product.

**Sections (top → bottom):**
- **Nav** — back ("Recap") + overflow (dots) menu.
- **Slide 1 — Final result** — split AR/MX diagonal background, both teams + flags, final score (`1 – 0`), "FINAL" label, competition + venue + date.
- **Slide 2 — Prediction stats** — accent background with confetti; two stat blocks ("68% de los fans acertó el resultado", "68% predijo lo mismo que vos") and the user's own pick ("Argentina 1 – 0 México") with a check.
- **Slides 3–N — Match moments** — each a labeled moment (Inicio del partido, ⚽ Gol · Argentina, Entretiempo, Fin del partido, 🏆 Resumen final) with a sub-line (minute, scorer, photo count) and a horizontal strip of portrait photo thumbnails tagged with the uploader's `@handle`.
- **Customization panel** —
  - **Slides** count: `3 / 5 / 8` (maps to 2 / 3 / 5 visible moments).
  - **Tone**: Emocionante / Inspirador / Humorístico / Nostálgico — recolors the whole screen accent **and** drives the AI narrative voice.
  - **Share**: Instagram / WhatsApp / X / copy-link + primary "Compartir recap completo".

**State (from the design):** `slideCount` (3/5/8), `tone` (4 options). Tone maps to an
accent palette applied across slide 2, moment markers, and CTAs.

## New capability vs feature-04

The recap is **user-customizable**: `tone` and `length (slideCount)` become inputs
to the AI generation in feature-04. Tone changes both the visual accent and the
voice Claude writes in. feature-04's recap endpoint must accept `tone` and a
target length and reflect them in the generated narrative + number of moment slides.

## Acceptance Criteria

- [ ] Recap screen renders all sections faithfully, reusing existing CSS tokens.
- [ ] Final-result slide shows teams, score, FINAL, venue + date.
- [ ] Prediction-stats slide shows the two percentages and the user's pick with a confirmed check.
- [ ] Match-moment slides render labeled moments with photo strips + uploader handles.
- [ ] Slides selector (3/5/8) changes the number of moment slides shown (2/3/5).
- [ ] Tone selector switches the accent palette across the screen and is passed to the recap generation.
- [ ] Share row renders IG / WhatsApp / X / copy + the "Compartir recap completo" CTA.
- [ ] `node --check` passes; page serves with no console errors (mock data inline).

## Notes

- Mock data inline (final score, prediction stats, moments + photos), same as the other screens — no live feeds in MVP.
- Wire to: feature-04 (AI narrative + labeled highlights, now tone/length-aware), feature-03 (Hype Wall photos per moment), feature-02 (prediction outcomes for the stats slide).
- Share = generate a shareable image/link; mock for the MVP, real if time allows.
- Apply QAF skills: front-end conventions in `code-conventions`; keep it framework-free to match `fanfest/frontend`.
