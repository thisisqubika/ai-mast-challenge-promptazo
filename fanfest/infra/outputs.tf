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

output "secret_param_names" {
  description = "Push real values with: aws ssm put-parameter --name <name> --type SecureString --value <value> --overwrite"
  value = {
    api_football_key  = aws_ssm_parameter.api_football_key.name
    anthropic_api_key = aws_ssm_parameter.anthropic_api_key.name
  }
}
