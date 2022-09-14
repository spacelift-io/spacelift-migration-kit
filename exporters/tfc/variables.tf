variable "export_state" {
  default     = true
  description = "Export Terraform state to files?"
  type        = bool
}

variable "tfc_organization" {
  description = "TFC/TFE organization name"
  type        = string
}

variable "vcs_default_branch" {
  default     = "main"
  description = "Name of the repositories' default branch"
  type        = string
}

variable "vcs_namespace" {
  default     = ""
  description = "The name of the entity containing the repository. The value should be empty for GitHub.com, the user/organization for GitHub (custom application), the project for Bitbucket, and the namespace for Gitlab."
  type        = string
}

variable "vcs_provider" {
  default     = "github"
  description = "Name of the Version Control System (VCS) provider to use"
  type        = string
}
