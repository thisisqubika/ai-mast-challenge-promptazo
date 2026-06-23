variable "aws_profile" {
  description = "AWS named profile to use"
  type        = string
  default     = "qubika-playground"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Resource name prefix"
  type        = string
  default     = "fanfest"
}

variable "image_tag" {
  description = "ECR image tag App Runner deploys"
  type        = string
  default     = "latest"
}

variable "frontend_origin" {
  description = "Cloudflare Pages origin allowed by backend CORS"
  type        = string
  default     = "https://fanfest.pages.dev"
}
