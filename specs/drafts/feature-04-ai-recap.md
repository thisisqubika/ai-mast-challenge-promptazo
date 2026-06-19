# Feature 04 — AI Recap (Hero Feature)

**Flow steps:** 7–10 · **Risk hint:** MEDIUM · **Strategy:** PLAN_FIRST
**AI in product:** YES — Claude API generates highlights + narrative recap · **Slice:** UI → API → AI

## Description

The post-event experience and the product's differentiator. After the match ends,
the app enters Recap mode and produces a personalized, AI-generated summary of the
fan fest. This is the **visible, explainable AI moment** the jury scores.

The AI does two things:
1. **Identifies highlights** of the event, labeled by moment — e.g. "Previa al
   partido", "Momento penal", "Antes del gol".
2. **Writes a narrative recap** ("crónica épica") personalized from event context:
   venue, date, attendee count, uploaded photos, final score.

The recap screen displays:
- **Resultado final** del partido — and reveals **who got their prediction right** (Feature 02).
- **Wrap up** del evento (the AI narrative).
- **Carrousel de fotos** (best photos from the Hype Wall).
- Social actions: **share to social, react, add comments**.
- **Sugerencias de próximos eventos** before the flow ends.

## Acceptance Criteria

- [ ] `POST /api/v1/events/{id}/recap` calls the Claude API with event context (venue, date, attendees, score, photos) and returns a narrative recap.
- [ ] The recap response includes labeled **highlights** ("Previa al partido", "Momento penal", "Antes del gol", etc.).
- [ ] Recap screen shows: final result, AI narrative wrap-up, and a photo carousel from the Hype Wall.
- [ ] Final result reveals **which users predicted correctly**.
- [ ] User can **share** the recap, **react**, and **add comments**.
- [ ] Recap ends with **next-event suggestions** (mocked recommendations are fine).
- [ ] A loading state ("Analizando la vibra del evento...") shows while the recap generates.
- [ ] Recap generation is resilient — if the AI call fails, show a graceful fallback (cached/templated summary) so the demo never breaks.

## AI / QAF notes

- Model: latest Claude (e.g. `claude-opus-4-8` or `claude-sonnet-4-6`) via Anthropic API. Key in `.env` as `ANTHROPIC_API_KEY`.
- Keep the prompt explainable: feed structured event context, ask for (a) labeled highlights and (b) a short personal narrative. Document the prompt in the README's "How AI Was Used" section.
- This slice is where the demo earns the **"AI is visible and explainable"** points — prioritize it and rehearse the live path.
- Suggested files: `fanfest/backend/app/services/recap_service.py` (Claude call),
  `events.py` recap endpoint, frontend recap view + carousel + comments.
