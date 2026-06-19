# Fan Fest — Product Context (for QAF)

This folder is the **human-authored product context** for the Fan Fest project.
It is the source material QAF and Claude Code should read to understand *what
needs to be built and why* before generating tickets or implementing features.

> QAF's own auto-generated knowledge base lives in `docs/llm-wiki/` (created by
> `/initialize-project`). This folder complements it with product intent, not
> codebase facts.

## How to use this with QAF

We use QAF for **both** planning and implementation:

1. Read the context docs below to understand the product and constraints.
2. Feature briefs live in [`/specs/drafts`](../../specs/drafts) — one per vertical slice.
3. **Plan**, then **implement** each slice:
   ```bash
   # PLAN: refine a draft brief into a canonical SDD ticket
   /create-sdd-ticket --from-markdown ./specs/drafts/feature-01-event-discovery.md \
                      --save-to-markdown ./specs/tickets/FEST-01-event-discovery.md
   # IMPLEMENT: build the planned ticket
   /implement-ticket --from-markdown ./specs/tickets/FEST-01-event-discovery.md
   ```
   Run `/initialize-project` once first so planning has project context to consult.
   See [`/specs/README.md`](../../specs/README.md) for the full workflow.

## Context docs

| File | What it covers |
|---|---|
| [`overview.md`](./overview.md) | Product vision, challenge constraints, MVP scope (in/out) |
| [`user-flow.md`](./user-flow.md) | Canonical end-to-end user flow (FigJam "Flujo" page, v2) |
| [`benchmark.md`](./benchmark.md) | Competitor research and what to borrow |

## Source of truth

- **Flow**: Benchmark FigJam → "Flujo" page (latest). Page 1 holds the earlier draft; "Flujo" supersedes it.
- **Screens / UI**: claude.ai/design project "Tribuna Fan Fests Discovery" (`60abb423-7365-4d4a-a03c-f14305f91d8b`) — one `*.dc.html` per screen (Home, Event Detail, …). Ported to `fanfest/frontend`.
- **Challenge rules**: Confluence — *Overview & Registration* + *Delivery Requirements* (TGS space).
