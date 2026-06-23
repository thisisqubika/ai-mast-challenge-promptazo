# Deploy FanFest

Hybrid: static frontend on **Cloudflare Pages**, FastAPI backend on **AWS App
Runner** with media on **S3 + CloudFront**.

```
Cloudflare Pages (frontend)  ──HTTPS+CORS──►  App Runner (backend, Docker)
                                                   │  boto3 (instance role)
                                                   ▼
                                              S3 (private)  ◄── CloudFront (OAC) ──► browser loads media
```

## 1. Backend + media → AWS (Terraform)

Everything lives in `infra/`. See `infra/README.md` for details.

```bash
cd fanfest/infra
./deploy.sh
```

Outputs you need:
- `backend_url` → the App Runner HTTPS endpoint
- `media_base_url` → CloudFront domain (already injected into the backend env)

## 2. Frontend → Cloudflare Pages

Set the backend origin in `fanfest/frontend/assets/js/config.js`:

```js
window.FANFEST_API_BASE = "https://<backend_url from terraform>";
```

Deploy the static folder:

```bash
cd fanfest/frontend
npx wrangler pages deploy . --project-name fanfest
```

Make sure the resulting `*.pages.dev` origin matches `var.frontend_origin` in
`infra/variables.tf` (it feeds the backend `CORS_ORIGINS`). Re-apply Terraform
if you change it.

## Local dev (unchanged)

`config.js` defaults to `http://localhost:8000`; the backend defaults to the
local-disk/`mock` media backend. No edits needed to run locally.
