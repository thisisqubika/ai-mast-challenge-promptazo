# Backend secrets, resolved at runtime by App Runner from SSM Parameter Store.
#
# Terraform manages the parameter resources (name, type) but NOT their values:
# the real secrets are pushed out-of-band with `aws ssm put-parameter --overwrite`
# so they never land in Terraform state or git. The PLACEHOLDER is written once
# on create and ignored on every apply thereafter.

resource "aws_ssm_parameter" "api_football_key" {
  name  = "/${local.name}/API_FOOTBALL_KEY"
  type  = "SecureString"
  value = "PLACEHOLDER"

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "anthropic_api_key" {
  name  = "/${local.name}/ANTHROPIC_API_KEY"
  type  = "SecureString"
  value = "PLACEHOLDER"

  lifecycle {
    ignore_changes = [value]
  }
}
