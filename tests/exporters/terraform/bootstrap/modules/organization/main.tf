terraform {
  required_version = "~> 1.0"

  required_providers {
    tfe = {
      source  = "hashicorp/tfe"
      version = "~> 0.49.2"
    }
  }
}

variable "github_oauth_token" {
  default     = null
  description = "GitHub OAuth token"
  nullable    = true
  type        = string
}

variable "name" {
  description = "Name of the organization"
  type        = string
}

variable "policy_sentinel_mandatory_enforcement" {
  default     = "soft"
  description = "Type of mandatory enforcement for Sentinel policies. Valid values: hard, soft."
  type        = string
}

variable "policy_type" {
  default     = "opa"
  description = "Type of policy to create. Valid values: opa, sentinel."
  type        = string
}

variable "tf_edition" {
  default     = "tfc_free"
  description = "Terraform Cloud/Enterprise edition. Valid values: tfc_free, tfc_standard, tfc_plus, tfe."
  type        = string
}
