# Infra 03 — Deploy Frontend to GitHub Pages

**Track:** Infra / DevOps · **Risk hint:** LOW · **Strategy:** DIRECT
**Depends on:** nothing (frontend is static and real today) · runs independently of the backend
**Decision context:** approved to deploy live now via GitHub Pages — zero config, repo already public, no account or token secrets. Earns the Delivery-Requirements "live deployment" extra points immediately.

## Description

Publish the static Tribuna Home frontend to a live URL via GitHub Pages, deployed
automatically by GitHub Actions on every push to `main`.

- `.github/workflows/deploy-pages.yml`:
  - Trigger: `push` to `main` (optionally scoped to `fanfest/frontend/**`).
  - No build step (vanilla HTML/CSS/JS): upload `fanfest/frontend` as the Pages artifact.
  - Use `actions/upload-pages-artifact` + `actions/deploy-pages`.
  - `permissions: { pages: write, id-token: write, contents: read }`, `environment: github-pages`.

## Acceptance Criteria

- [ ] Push to `main` publishes the frontend to a live GitHub Pages URL.
- [ ] The deployed page renders the Tribuna Home screen (CDN fonts/icons load over HTTPS).
- [ ] Workflow uses least-privilege permissions and the official Pages actions.
- [ ] Live URL is documented in the README (and the write-up).

## Notes

- **Human step:** enable Pages in repo settings → Source = "GitHub Actions" (one-time). Flag this to the captain.
- Backend deploy is intentionally out of scope here — wait until the backend has real endpoints (revisit after product/QAF implement features). Could later move to Railway/Render for the full stack.
- Apply QAF skills: `github-actions-secure-ci-cd-pipelines`.
