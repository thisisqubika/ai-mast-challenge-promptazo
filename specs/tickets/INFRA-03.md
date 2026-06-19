# INFRA-03: Deploy Static Frontend to GitHub Pages via GitHub Actions

## User Story

**As a** FanFest captain (project owner / reviewer)
**I want** the static Tribuna Home frontend published to a live, public URL automatically on every push to `main`
**So that** reviewers can open the running app without a local checkout, and the project earns the Delivery-Requirements "live deployment" points immediately.

## Stakeholders

- **Captain / Reviewer** — owns the one-time repo setting (Pages Source = "GitHub Actions") and acceptance of the live URL.
- **Infra / DevOps engineer** — authors and maintains the deploy workflow.
- **Frontend contributors** — benefit from automatic publish on merge; no manual deploy step.

## Success Criteria

1. A push to `main` triggers the workflow and publishes `fanfest/frontend` to a live GitHub Pages URL (`https://thisisqubika.github.io/ai-mast-challenge-promptazo/`).
2. The deployed page renders the Tribuna Home screen with CDN fonts (Google Fonts: Inter) and icons (jsDelivr: Tabler) loading over HTTPS.
3. The workflow uses least-privilege permissions (`pages: write`, `id-token: write`, `contents: read`) and the official first-party Pages actions.
4. The live URL is documented in `README.md` (and the project write-up).

## Acceptance Criteria

### Scenario 1: Happy path — push to main publishes the frontend

```gherkin
Given the repository is public and Pages Source is set to "GitHub Actions"
And the workflow .github/workflows/deploy-pages.yml exists on main
When a commit is pushed to the main branch
Then the deploy-pages workflow runs to completion successfully
And the contents of fanfest/frontend are published to https://thisisqubika.github.io/ai-mast-challenge-promptazo/
And opening that URL returns HTTP 200 with the Tribuna Home index.html
```

### Scenario 2: Deployed page renders with external assets over HTTPS

```gherkin
Given the frontend has been published to GitHub Pages
When a visitor opens the live GitHub Pages URL in a browser
Then the Tribuna Home screen renders
And the Inter font from https://fonts.googleapis.com loads over HTTPS
And the Tabler icon webfont from https://cdn.jsdelivr.net loads over HTTPS
And the relative assets ./assets/css/main.css and ./assets/js/main.js resolve correctly under the /ai-mast-challenge-promptazo/ project subpath
```

### Scenario 3: Least-privilege workflow using official Pages actions

```gherkin
Given the deploy-pages.yml workflow definition
When the workflow is inspected
Then top-level permissions grant only pages: write, id-token: write, contents: read
And the deploy job declares environment: github-pages
And the artifact is uploaded with actions/upload-pages-artifact (no build step)
And the deployment uses actions/deploy-pages
And no custom personal access token or repository secret is referenced
```

### Scenario 4: Edge — push that touches only the backend

```gherkin
Given the workflow trigger is scoped to push on main for fanfest/frontend/**
When a commit changes only files under fanfest/backend/**
Then the deploy-pages workflow is not triggered for that push
And the previously published frontend remains live and unchanged
```

### Scenario 5: Failure — Pages not yet enabled in repo settings

```gherkin
Given Pages Source has not been set to "GitHub Actions" in repo settings
When the deploy-pages workflow runs on a push to main
Then the deploy-pages step fails with a clear "Pages not enabled" error
And the failure is visible in the Actions tab so the captain can perform the one-time enablement
```

## Technical Context

- **Current state**
  - `fanfest/frontend` is a static site: `index.html`, `assets/css/main.css`, `assets/js/main.js`, `assets/js/api.js`. No bundler, no build step (per `.claude/CLAUDE.md`: vanilla JS, no bundler).
  - `index.html` references external CDN assets over HTTPS: Google Fonts (Inter) and jsDelivr (`@tabler/icons-webfont@3.21.0`). Local assets use relative paths (`./assets/css/main.css`, `./assets/js/main.js`).
  - No `.github/workflows/` directory exists yet.
  - Remote is `github.com:thisisqubika/ai-mast-challenge-promptazo` on the `main` branch; the repo is public.
  - Backend (`fanfest/backend`) is a stub today and is intentionally not deployed here.

- **Proposed changes**
  - Add `.github/workflows/deploy-pages.yml`:
    - Trigger: `push` to `main`, path-scoped to `fanfest/frontend/**` (plus the workflow file itself), with `workflow_dispatch` for manual runs.
    - No build step — upload `fanfest/frontend` directly as the Pages artifact via `actions/upload-pages-artifact`, then deploy with `actions/deploy-pages`.
    - Top-level `permissions: { pages: write, id-token: write, contents: read }`.
    - Deploy job sets `environment: github-pages` and exposes the deployment URL.
    - Add a `concurrency` group (e.g. `group: pages`, `cancel-in-progress: false`) so overlapping pushes do not race.
  - Add the live URL to `README.md` (and the write-up).

- **Constraints**
  - Least-privilege permissions only; no custom PATs or repository secrets (none are needed for public Pages via the official actions).
  - Pin the official Pages actions to a known major version.
  - Relative asset paths must continue to resolve under the project subpath `/ai-mast-challenge-promptazo/`; do not introduce root-absolute (`/assets/...`) paths.

- **Integration points**
  - GitHub Actions runner, GitHub Pages environment (`github-pages`).
  - External CDNs (Google Fonts, jsDelivr) consumed at page load — not part of the deploy artifact.

- **Architecture decisions**
  - **Decision:** Deploy via GitHub Actions Pages flow (`upload-pages-artifact` + `deploy-pages`) rather than the legacy branch-based Pages. **Rationale:** zero extra config, OIDC-based, least-privilege, first-party actions; repo is already public.
  - **Decision:** No build step. **Rationale:** the frontend is vanilla HTML/CSS/JS; uploading the directory as-is is the simplest correct approach.
  - **Decision:** Path-scope the trigger to `fanfest/frontend/**`. **Rationale:** avoids redundant redeploys on backend-only commits.
  - **Decision:** Deploy frontend only; backend remains out of scope. **Rationale:** backend has no real endpoints yet; revisit (e.g. Railway/Render) once features land.

## Out Of Scope

- Backend deployment (no real endpoints yet; revisit later, possibly Railway/Render for the full stack).
- Custom domain / DNS configuration for Pages.
- Any frontend build tooling, bundler, or asset minification pipeline.
- Self-hosting the CDN fonts/icons locally.
- The one-time manual repo setting (Pages Source = "GitHub Actions") is an operator action, not a code deliverable — see Implementation Notes.

## Edge Cases And Error Handling

- **Edge — backend-only commit:** path-scoped trigger prevents an unnecessary redeploy; the live frontend is unaffected.
- **Edge — project subpath:** the site is served from `/ai-mast-challenge-promptazo/`, not the domain root; relative asset paths already handle this, so no `<base>` tag or path rewrite is required. Verify no asset 404s after the first deploy.
- **Error — Pages not enabled:** the `deploy-pages` step fails with a "Pages not enabled" / "Get Pages site failed" error until the captain sets Source = "GitHub Actions" once.
- **Error — CDN unreachable at view time:** Google Fonts / jsDelivr outage degrades fonts/icons but the page still renders with fallback fonts; this is a runtime CDN concern, not a deploy failure.
- **Error — concurrent pushes:** the `concurrency` group serializes deployments so a later push does not clobber an in-flight one.

### Validation Rules

- Workflow top-level `permissions` must contain exactly `pages: write`, `id-token: write`, `contents: read` and nothing broader.
- Workflow must reference only `actions/upload-pages-artifact` and `actions/deploy-pages` (plus `actions/configure-pages` / `actions/checkout` as needed) — no third-party deploy actions, no secrets.
- The deployed root URL must return HTTP 200 and serve `fanfest/frontend/index.html`.

## Dependencies

- **Blocking:** none. The frontend is static and real today; this runs independently of the backend.
- **Related:**
  - INFRA-01 — CI and backend health (separate CI pipeline).
  - INFRA-02 — Docker / docker compose (local full-stack run; independent of Pages).

## Definition Of Done

- **Code quality**
  - `.github/workflows/deploy-pages.yml` added with least-privilege `permissions`, `environment: github-pages`, path-scoped `push` trigger, and a `concurrency` group.
  - Official first-party Pages actions only, pinned to a major version; no secrets or PATs referenced.
- **Testing / verification**
  - A push to `main` produces a green workflow run.
  - The live URL `https://thisisqubika.github.io/ai-mast-challenge-promptazo/` returns 200 and renders the Tribuna Home screen.
  - Browser network panel confirms Google Fonts and Tabler icons load over HTTPS and local assets resolve under the project subpath (no 404s).
  - Confirmed that a backend-only commit does not trigger the workflow.
- **Documentation**
  - Live URL added to `README.md` and the project write-up.
- **Review and deployment**
  - Workflow reviewed and approved.
  - Captain has performed the one-time Pages enablement (Source = "GitHub Actions").

## Wiki Evidence

- Wiki preload skipped (`--skip-wiki`): wiki unavailable — fell back to convention skills + `.claude/CLAUDE.md` only.
- `.claude/CLAUDE.md` — frontend is vanilla JS with no bundler; frontend lives at `fanfest/frontend`.

## Graph Evidence

- Phase 5a impact-radius check skipped — the change is a net-new workflow file plus one README line; no existing code files are touched, so there are no inferable primary files to query. Subjective "Small" evaluation applied instead (well under 1 day).
- Codebase inspection (grep / file listing): `fanfest/frontend` contains only `index.html` + `assets/{css,js}`; `index.html` references Google Fonts and jsDelivr over HTTPS with relative local asset paths; no `.github/workflows/` directory exists; remote is `thisisqubika/ai-mast-challenge-promptazo` on `main`.

## Implementation Notes

- **Human step (flag to the captain):** one-time enable Pages in repo settings → Source = "GitHub Actions". The workflow cannot do this; the first run will fail until it is set.
- Suggested workflow shape: a `build`/upload job (`actions/configure-pages` + `actions/upload-pages-artifact` with `path: fanfest/frontend`) and a separate `deploy` job (`environment: github-pages`, `actions/deploy-pages`).
- Pin actions to a major version (e.g. `@v3` for `upload-pages-artifact`, `@v4` for `deploy-pages`) and confirm current majors at implementation time.
- Apply the QAF skill `github-actions-secure-ci-cd-pipelines` when authoring the workflow (least-privilege permissions, pinned actions, OIDC `id-token`).
- Keep local asset references relative; do not switch to root-absolute paths, which would break under the `/ai-mast-challenge-promptazo/` subpath.

## References

- Draft source: `specs/drafts/infra-03-deploy-frontend-pages.md`
- QAF skill: `github-actions-secure-ci-cd-pipelines`
- GitHub Pages via Actions: `actions/upload-pages-artifact`, `actions/deploy-pages`, `actions/configure-pages`

---

**INVEST Validated**: ✅ (Independent: no blocking deps; Negotiable: trigger scoping/pinning open; Valuable: live reviewable URL + delivery points; Estimable: single workflow file + doc line; Small: < 1 day, net-new workflow only; Testable: live URL returns 200 and renders)
**BDD Scenarios**: 5
