# Access role: lets App Runner pull the image from ECR.
data "aws_iam_policy_document" "apprunner_access_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["build.apprunner.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "apprunner_access" {
  name               = "${local.name}-apprunner-access"
  assume_role_policy = data.aws_iam_policy_document.apprunner_access_assume.json
}

resource "aws_iam_role_policy_attachment" "apprunner_ecr" {
  role       = aws_iam_role.apprunner_access.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

# Instance role: the running container's identity (boto3 uses it for S3).
data "aws_iam_policy_document" "apprunner_instance_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["tasks.apprunner.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "apprunner_instance" {
  name               = "${local.name}-apprunner-instance"
  assume_role_policy = data.aws_iam_policy_document.apprunner_instance_assume.json
}

data "aws_iam_policy_document" "media_rw" {
  statement {
    actions   = ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"]
    resources = ["${aws_s3_bucket.media.arn}/*"]
  }
}

resource "aws_iam_role_policy" "apprunner_media" {
  name   = "${local.name}-media-rw"
  role   = aws_iam_role.apprunner_instance.id
  policy = data.aws_iam_policy_document.media_rw.json
}

# Read backend secrets from SSM. App Runner resolves runtime_environment_secrets
# using the instance role; SecureString params also need kms:Decrypt on the
# AWS-managed aws/ssm key.
data "aws_kms_alias" "ssm" {
  name = "alias/aws/ssm"
}

data "aws_iam_policy_document" "secrets_read" {
  statement {
    actions = ["ssm:GetParameters"]
    resources = [
      aws_ssm_parameter.api_football_key.arn,
      aws_ssm_parameter.anthropic_api_key.arn,
    ]
  }
  statement {
    actions   = ["kms:Decrypt"]
    resources = [data.aws_kms_alias.ssm.target_key_arn]
  }
}

resource "aws_iam_role_policy" "apprunner_secrets" {
  name   = "${local.name}-secrets-read"
  role   = aws_iam_role.apprunner_instance.id
  policy = data.aws_iam_policy_document.secrets_read.json
}
