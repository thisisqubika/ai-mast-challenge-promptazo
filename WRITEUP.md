# Fan Fest — Project Write-up

*Qubika AI Mastery Challenge, World Cup Edition 2026 · Track: Fan Experience*

## What problem we tried to solve

Watching football with other fans is one of the best parts of the sport, but the logistics around it are scattered and frustrating. Fans across Latin America improvise every week: a WhatsApp group here, a Facebook event there, a bar everyone defaults to out of habit. There is no single place to find a watch party near you, decide it's worth going to, coordinate getting there, and keep the memory of it afterward. Every existing tool solves one slice and stops at the final whistle.

## What we built

Fan Fest is a community-driven web platform that follows a fan through the entire arc of a match-day gathering:

- **Discover** fan festivals near you or in a chosen city, with visual, vibe-first event cards.
- **Join** in one tap (RSVP), with the attendee list visible as social proof.
- **Coordinate** — save the date to Google Calendar and open turn-by-turn navigation to the venue via Google Maps.
- **Share** — during the match, upload photos to a live "Hype Wall" gallery backed by Google Drive.
- **Relive** — after the final whistle the app flips to a post-event mode and generates a personalized **AI Recap**: the final score, an epic AI-written chronicle of the gathering, and a carousel of the best photos.

The AI Recap is the hero moment. It is what no competitor offers: closing the loop from discovery all the way to a shared memory.

## How we used AI to build it

- **Claude Code CLI** drove development end-to-end from the terminal: scaffolding the FastAPI backend and the frontend, generating API routes, and iterating on bugs through natural-language prompts.
- **QAF (Qubika Agentic Framework)**, our mandatory technical foundation, ran `initialize-project` to analyze the repo and auto-generate project configuration, and `implement-ticket` to delegate feature work to Claude Code agents following spec-driven tickets.
- **Claude API in the product** generates the recap narrative from event context (location, date, attendance, score, photos).
- **What surprised us:** the recap quality with minimal prompt engineering. A short prompt describing the event context produced narrative text that felt genuinely personal on the first try, where we had budgeted for several rounds of iteration.

## What we'd do next with another week

- Real-time match data (live score, goal cards with the scorer) feeding the in-event screen.
- Smart discovery: AI matching fans to nearby fests by team allegiance and vibe, not just proximity.
- Push notifications for kickoff, goals, and "your recap is ready."
- Private invite-by-link fests for small watch parties, with no account required to RSVP.

---

*Draft — refine with final build state, screenshots, and demo link before the submission deadline.*
