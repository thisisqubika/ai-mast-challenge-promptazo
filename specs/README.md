# Fan Fest — Feature Specs (QAF plan + implement)

We use QAF for **both** planning and implementation. This folder holds the inputs
and outputs of that two-step flow.

```
specs/
  drafts/    ← human-authored feature briefs (one vertical slice each) — INPUT to planning
  tickets/   ← QAF-generated canonical SDD tickets — OUTPUT of planning, INPUT to implementation
```

Read the product context first: [`docs/product/`](../docs/product). Canonical flow:
[`docs/product/user-flow.md`](../docs/product/user-flow.md).

## Workflow

```bash
# 0. One-time — generate QAF project knowledge (docs/llm-wiki/ + CLAUDE.md)
/initialize-project

# 1. PLAN — refine a draft brief into a full SDD ticket (BDD scenarios, gap detection, INVEST, DoD)
/create-sdd-ticket --from-markdown ./specs/drafts/feature-01-event-discovery.md \
                   --save-to-markdown ./specs/tickets/FEST-01-event-discovery.md

# 2. IMPLEMENT — build the planned ticket
/implement-ticket --from-markdown ./specs/tickets/FEST-01-event-discovery.md
```

> On a freshly cloned repo with no wiki yet, add `--skip-wiki` to `/create-sdd-ticket`,
> or run `/initialize-project` first so planning has project context to consult.

## Drafts (build order)

| # | Draft | Flow steps | Demo value |
|---|---|---|---|
| 1 | [`drafts/feature-01-event-discovery.md`](./drafts/feature-01-event-discovery.md) | 1–2 | Home feed of nearby fan fests |
| 2 | [`drafts/feature-02-event-details-rsvp.md`](./drafts/feature-02-event-details-rsvp.md) | 3–4 | Event detail, share/invite, predict, check-in |
| 3 | [`drafts/feature-03-live-event-hype-wall.md`](./drafts/feature-03-live-event-hype-wall.md) | 5–6 | Live scoreboard + Hype Wall photo upload |
| 4 | [`drafts/feature-04-ai-recap.md`](./drafts/feature-04-ai-recap.md) | 7–10 | **AI recap** — the hero / AI moment |
| 5 | [`drafts/feature-05-event-detail-screen.md`](./drafts/feature-05-event-detail-screen.md) | 3–6 | Event Detail (Previa) screen — UI for features 02 + 03 |
| 6 | [`drafts/feature-06-recap-screen.md`](./drafts/feature-06-recap-screen.md) | 7–10 | Recap screen — UI for feature 04 (tone + length customization) |

Slices are independent enough to demo on their own, but the end-to-end story
(discover → join → live → recap) is what the jury scores. Slice 4 carries the
"visible, explainable AI" requirement — prioritize it.

## Infra / DevOps track (build now, while product defines features)

CI/CD groundwork, captured as drafts so it runs through the same QAF plan→implement
flow. Decisions already made: GitHub Pages deploy, Docker `compose up` now, minimal
backend `/health` so the pipeline runs green.

| # | Draft | What |
|---|---|---|
| 1 | [`drafts/infra-01-ci-and-backend-health.md`](./drafts/infra-01-ci-and-backend-health.md) | GitHub Actions CI + minimal FastAPI `/health` |
| 2 | [`drafts/infra-02-docker-compose.md`](./drafts/infra-02-docker-compose.md) | Backend Dockerfile + `docker compose up` (serves frontend too) |
| 3 | [`drafts/infra-03-deploy-frontend-pages.md`](./drafts/infra-03-deploy-frontend-pages.md) | Auto-deploy static frontend to GitHub Pages |

Order: infra-01 → infra-02 (depends on the health app); infra-03 is independent
and can ship anytime. Backend deploy waits until the backend has real endpoints.

## Convention

- App code lives under `fanfest/` (backend: FastAPI in `fanfest/backend/app`, frontend: `fanfest/frontend`).
- Event/match data is **mocked** unless a draft says otherwise (no live third-party feeds in MVP).
- Drafts are the **plan input** — keep them as intent. Let `/create-sdd-ticket` produce the implementation-ready ticket in `tickets/`; don't hand-author tickets.
- Each draft notes its QAF risk hint and where the AI is used.
