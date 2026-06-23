# Pinned to a single instance: SQLite is on the (ephemeral) container disk and
# cannot be shared across instances. Move the DB to RDS to scale max_size > 1.
resource "aws_apprunner_auto_scaling_configuration_version" "single" {
  auto_scaling_configuration_name = "${local.name}-single"
  max_concurrency                 = 100
  min_size                        = 1
  max_size                        = 1
}

resource "aws_apprunner_service" "backend" {
  service_name = "${local.name}-backend"

  source_configuration {
    auto_deployments_enabled = false

    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_access.arn
    }

    image_repository {
      image_identifier      = "${aws_ecr_repository.app.repository_url}:${var.image_tag}"
      image_repository_type = "ECR"

      image_configuration {
        port = "8000"
        runtime_environment_variables = {
          MEDIA_STORAGE_BACKEND = "s3"
          S3_BUCKET             = aws_s3_bucket.media.bucket
          MEDIA_BASE_URL        = "https://${aws_cloudfront_distribution.media.domain_name}"
          AWS_REGION            = var.region
          CORS_ORIGINS          = var.frontend_origin
        }
        runtime_environment_secrets = {
          API_FOOTBALL_KEY  = aws_ssm_parameter.api_football_key.arn
          ANTHROPIC_API_KEY = aws_ssm_parameter.anthropic_api_key.arn
        }
      }
    }
  }

  instance_configuration {
    cpu               = "1024" # 1 vCPU
    memory            = "2048" # 2 GB — headroom for moviepy rendering
    instance_role_arn = aws_iam_role.apprunner_instance.arn
  }

  health_check_configuration {
    protocol = "HTTP"
    path     = "/health"
  }

  auto_scaling_configuration_arn = aws_apprunner_auto_scaling_configuration_version.single.arn
}
