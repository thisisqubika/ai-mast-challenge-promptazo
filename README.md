# Fan Fest

An end-to-end fan event platform — discover, RSVP, navigate, share photos, and relive football moments with a personalized AI recap.

> **Qubika AI Mastery Challenge — World Cup Edition 2026** · Track: Fan Experience
> The application lives in [`fanfest/`](./fanfest). See [`WRITEUP.md`](./WRITEUP.md) for the 1-page project story.

---

## The Problem

Football fans across Latin America watch matches together every week, but there's no dedicated place to find these gatherings, coordinate with other fans, or preserve the shared experience afterward. Existing platforms cover pieces of the problem — Eventbrite handles registration, Fever does visual discovery, Facebook Events handles photo sharing — but none of them combine all of these into a single fan journey, and none offer anything after the final whistle.

## The Solution

Fan Fest is a web platform that takes fans through the full arc of a watch party: discover events near you, RSVP in one tap, save the date to Google Calendar, open navigation directly to the venue via Google Maps, upload photos to a live gallery wall backed by Google Drive, and receive a personalized AI-generated recap after the match. The recap is the hero moment — a narrative summary that feels personal: *"Here's your Fan Fest at Estadio Kempes, June 18, with 47 fans and 3 goals."* No other platform closes the loop from discovery to memory.

## How AI Was Used

**In the product:**
Claude (Anthropic) generates the post-event AI recap via `POST /api/v1/events/{id}/recap`. Key design choices:

- **Structured JSON prompt:** event context (venue, date, teams, final score, goals list, photo count) is serialized to JSON and injected into a single prompt block, making the AI usage auditable and the output predictable.
- **Shaped output:** Claude is asked to return a JSON object with two keys — `highlights` (an array of `{label, description}` moment objects) and `narrative` (a short paragraph in Spanish). Callers control the number of highlights via `slide_count` (1–10) and the narrative voice via `tone` (`emocionante`, `inspirador`, `humorístico`, `nostálgico`).
- **Graceful fallback:** if the Anthropic API is unavailable (network error, quota, empty key), the endpoint returns a templated HTTP 200 response with `"fallback": true` — the demo never surfaces a 500 to the frontend.
- **Loading state:** the frontend shows "Analizando la vibra del evento..." while the recap generates, keeping the experience smooth even when the API call takes a few seconds.

**To build it:**
- **Claude Code CLI** was used end-to-end: scaffolding the project structure, generating backend API routes in FastAPI, writing frontend components, and iterating on bugs — all through natural-language prompts in the terminal.
- **QAF (Qubika Agentic Framework)** — our internal multi-agent framework built on LangGraph and Claude — ran the `initialize-project` workflow to analyze the repository and auto-generate the project configuration, and powered the `implement-ticket` skill to delegate feature development tasks to Claude Code agents.
- **What surprised us:** the quality of the AI recap with minimal prompt engineering. A short prompt describing event context, attendance, and score produced narrative text that felt genuinely personal on the first attempt. We expected to spend more time on prompt iteration.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI |
| Frontend | HTML, CSS, JavaScript |
| AI | Claude API (Anthropic) — event recap generation |
| Integrations | Google Calendar, Google Maps, Google Drive |
| Build tooling | Claude Code CLI, QAF (Qubika Agentic Framework) |

## How to Run It Locally

**Backend**

```bash
cd fanfest/backend
pip install -r requirements.txt
cp .env.example .env        # fill in ANTHROPIC_API_KEY and Google credentials
uvicorn app.main:app --reload
# API available at http://localhost:8000
```

**Frontend**

```bash
cd fanfest/frontend
python -m http.server 8080
# Open http://localhost:8080 in your browser
```

**Environment variables required** (see `fanfest/backend/.env.example`):
- `ANTHROPIC_API_KEY` — for the AI recap feature
- Google OAuth credentials — for Calendar, Maps, and Drive integrations

## Team

| Name | Role |
|---|---|
| Sofia Fleiderman | Product Designer |
| Nicolas Pisani | Product Designer |
| Rocio Talavera | Product Designer |
| Diego Flores | Data Scientist |
| Sebastian Demasi | SRE / DevOps Engineer |
| Paula Canepa | Data Scientist |
