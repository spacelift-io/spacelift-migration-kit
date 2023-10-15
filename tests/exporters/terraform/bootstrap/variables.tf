variable "api_token" {
  description = "Terraform Cloud/Enterprise API token"
  type        = string
}

variable "github_oauth_token" {
  default     = null
  description = "GitHub OAuth token"
  nullable    = true
  type        = string
}

variable "tf_edition" {
  default     = "tfc_free"
  description = "Terraform Cloud/Enterprise edition. Valid values: tfc_free, tfc_standard, tfc_plus, tfe."
  type        = string
}
