#!/usr/bin/env bash
# Build + push the backend image, then apply all infra.
# App Runner can't be created until the image exists in ECR, so this is staged.
set -euo pipefail
cd "$(dirname "$0")"

PROFILE="${AWS_PROFILE:-qubika-playground}"
REGION="${AWS_REGION:-us-east-1}"
TAG="${1:-latest}"
export AWS_PROFILE="$PROFILE"

# 1. Create the ECR repo first.
terraform init -input=false
terraform apply -input=false -auto-approve -target=aws_ecr_repository.app

REPO=$(terraform output -raw ecr_repo_url)
REGISTRY="${REPO%%/*}"

# 2. Build for App Runner (linux/amd64) and push.
aws ecr get-login-password --region "$REGION" --profile "$PROFILE" \
  | docker login --username AWS --password-stdin "$REGISTRY"
docker build --platform linux/amd64 -t "$REPO:$TAG" ../backend
docker push "$REPO:$TAG"

# 3. Apply everything else (S3, CloudFront, IAM, App Runner).
terraform apply -input=false -auto-approve -var "image_tag=$TAG"

echo
echo "Backend URL : $(terraform output -raw backend_url)"
echo "Media CDN   : $(terraform output -raw media_base_url)"
echo "Set window.FANFEST_API_BASE in frontend/assets/js/config.js to the Backend URL."
