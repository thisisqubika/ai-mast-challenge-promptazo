output "ecr_repo_url" {
  description = "Push the backend image here"
  value       = aws_ecr_repository.app.repository_url
}

output "backend_url" {
  description = "App Runner HTTPS endpoint — set as window.FANFEST_API_BASE"
  value       = "https://${aws_apprunner_service.backend.service_url}"
}

output "media_base_url" {
  description = "CloudFront domain media is served from"
  value       = "https://${aws_cloudfront_distribution.media.domain_name}"
}

output "media_bucket" {
  value = aws_s3_bucket.media.bucket
}
