# Tribuna

An end-to-end fan event platform: discover, RSVP, navigate, check in, share photos, follow the match live, and relive football moments with a personalized AI recap.

> **Qubika AI Mastery Challenge, World Cup Edition 2026** · Track: Fan Experience
> The application lives in [`fanfest/`](./fanfest). See [`WRITEUP.md`](./WRITEUP.md) for the 1-page project story.

---

## The Problem

Watching football with other fans is one of the best parts of the sport, but the logistics around it are scattered and frustrating. Fans across Latin America improvise every week: a WhatsApp group here, a Facebook event there, a bar everyone defaults to out of habit. There is no single place to find these gatherings, decide whether it's worth going, coordinate getting there, connect with other fans, and keep the memory of the shared experience afterward. Every existing tool solves one slice of the fan journey and stops at the final whistle.

## The Solution

Tribuna is a community-driven web platform that follows a fan through the entire arc of a match-day gathering. Fans discover events nearby, RSVP in one tap, save the date to Google Calendar, and open navigation to the venue via Google Maps. On match day they check in at the venue, contribute to a live photo wall, and follow the game through real-time score updates powered by API-Football. The recap is the hero moment: when the final whistle blows, the platform shifts into Recap mode and weaves fan photos with an AI-generated narrative that feels personal (for example, *"Here's your match-day at Estadio Kempes, June 18, with 47 fans and 3 goals"*), and can render the highlights into a short recap video. No other platform closes the loop from discovery to memory.

## How AI Was Used

**In the product:**
Claude (Anthropic) generates the post-event AI recap via `POST /api/v1/events/{id}/recap`. Key design choices:

- **Structured JSON prompt:** event context (venue, date, teams, final score, goals list, photo count) is serialized to JSON and injected into a single prompt block, making the AI usage auditable and the output predictable.
- **Shaped output:** Claude is asked to return a JSON object with two keys, `highlights` (an array of `{label, description}` moment objects) and `narrative` (a short paragraph in Spanish). Callers control the number of highlights via `slide_count` (1-10) and the narrative voice via `tone` (`emocionante`, `inspirador`, `humorístico`, `nostálgico`).
- **Graceful fallback:** if the Anthropic API is unavailable (network error, quota, empty key), the endpoint returns a templated HTTP 200 response with `"fallback": true`, so the demo never surfaces a 500 to the frontend.
- **Video recap:** `POST /api/v1/events/{id}/recap/video` renders the fan photos into a short highlight video with MoviePy and FFmpeg, then stores it on S3.
- **Loading state:** the frontend shows "Analizando la vibra del evento..." while the recap generates, keeping the experience smooth even when the API call takes a few seconds.

**To build it:**
- **Claude Code CLI** was used end-to-end: scaffolding the project structure, generating backend API routes in FastAPI, writing frontend components, and iterating on bugs, all through natural-language prompts in the terminal.
- **QAF (Qubika Agentic Framework)**, our internal multi-agent framework built on LangGraph and Claude, ran the `initialize-project` workflow to analyze the repository and auto-generate the project configuration, and powered the `implement-ticket` skill to delegate feature development tasks to Claude Code agents.
- **What surprised us:** the quality of the AI recap with minimal prompt engineering. A short prompt describing event context, attendance, and score produced narrative text that felt genuinely personal on the first attempt. We expected to spend more time on prompt iteration.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy (SQLite) |
| Frontend | HTML, CSS, vanilla JavaScript |
| AI | Claude API (Anthropic): recap narrative + highlights |
| Live match data | API-Football (real-time scores) |
| Media storage | Amazon S3 + CloudFront (private bucket, OAC) |
| Video recap | MoviePy + FFmpeg |
| Integrations | Google Calendar, Google Maps, Google Drive |
| Deployment | AWS App Runner (backend, Docker), Cloudflare Pages (frontend) |
| Build tooling | Claude Code CLI, QAF (Qubika Agentic Framework) |

## How to Run It Locally

**Backend**

```bash
cd fanfest/backend
pip install -r requirements.txt
cp .env.example .env        # fill in your API keys (see Environment variables below)
uvicorn app.main:app --reload
# API available at http://localhost:8000
```

**Frontend**

```bash
cd fanfest/frontend
python -m http.server 8080
# Open http://localhost:8080 in your browser
```

Locally, media defaults to the on-disk backend (`MEDIA_STORAGE_BACKEND=local`), so no AWS credentials are needed to run the app.

**Environment variables** (see `fanfest/backend/.env.example`):
- `ANTHROPIC_API_KEY` — AI recap feature. Get it at [console.anthropic.com](https://console.anthropic.com) → API Keys.
- `API_FOOTBALL_KEY` — optional, enables real-time score updates. Get it at [dashboard.api-football.com](https://dashboard.api-football.com) (free tier, 100 req/day).

## Deployment

Production runs as a hybrid: the static frontend on **Cloudflare Pages**, the FastAPI backend on **AWS App Runner** (Docker), and media on a **private S3 bucket served through CloudFront** (Origin Access Control). Infrastructure is defined with Terraform in [`fanfest/infra/`](./fanfest/infra); see [`fanfest/DEPLOY.md`](./fanfest/DEPLOY.md) for the full setup.

## Team

| Name | Role |
|---|---|
| Sofia Fleiderman | Product Designer |
| Nicolas Pisani | Product Designer |
| Rocio Talavera | Product Designer |
| Diego Flores | Data Scientist |
| Sebastian Demasi | SRE / DevOps Engineer |
| Paula Canepa | Data Scientist |
