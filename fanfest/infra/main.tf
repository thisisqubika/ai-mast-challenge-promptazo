data "aws_caller_identity" "me" {}

locals {
  name        = var.project
  bucket_name = "${var.project}-media-${data.aws_caller_identity.me.account_id}"
}
