# FanFest AWS infra (Terraform)

Backend on **AWS App Runner**, media on **S3 + CloudFront**, image in **ECR**.
Frontend stays on **Cloudflare Pages** (see `../DEPLOY.md`).

AWS profile: `qubika-playground` (us-east-1). Override with `AWS_PROFILE` / `var.region`.

## What it creates

| Resource | Purpose |
|---|---|
| ECR repo | holds the backend Docker image |
| App Runner service | runs the FastAPI container (1 vCPU / 2 GB, **pinned to 1 instance**) |
| S3 bucket (private) | media storage (photos + rendered recap videos) |
| CloudFront + OAC | serves media; bucket stays private |
| IAM roles | App Runner ECR-pull (access) + S3 read/write (instance) |

## Deploy

```bash
cd fanfest/infra
./deploy.sh            # stages: ECR → build+push image → apply rest
```

The image is built `--platform linux/amd64` because App Runner runs x86.

Then point the frontend at the backend: copy the `backend_url` output into
`fanfest/frontend/assets/js/config.js` (`window.FANFEST_API_BASE`) and deploy
Pages. Make sure `var.frontend_origin` matches your Pages URL (it feeds the
backend `CORS_ORIGINS`).

## Manual apply (instead of the script)

```bash
terraform init
terraform apply -target=aws_ecr_repository.app   # 1. repo
# 2. build + push (see deploy.sh for the docker/ecr login lines)
terraform apply                                  # 3. everything else
```

## Notes / tradeoffs

- **SQLite is ephemeral.** It lives on the container disk, re-seeds on boot, and
  resets on every deploy/recycle. User predictions/check-ins don't persist.
  Media *does* persist (it's on S3). Move the DB to RDS to fix persistence and
  to raise `max_size` above 1.
- **No AI key wired.** Recap text uses `provider="auto"` and degrades without a
  key. To enable Claude, store `ANTHROPIC_API_KEY` in Secrets Manager and add a
  `runtime_environment_secrets` block to `apprunner.tf`.
- **CloudFront takes ~5–15 min** to deploy/propagate on first apply.

## Teardown

```bash
terraform destroy
```
