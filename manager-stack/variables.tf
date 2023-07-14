variable "branch" {
  default     = "main"
  description = "Name of the branch to associate with the stack"
  type        = string
}

variable "import_state" {
  default     = false
  description = "Import the Terraform state for the managed stacks into Spacelift?"
  type        = bool
}

variable "project_root" {
  default     = null
  description = "Path to the folder containing the Terraform code, in case of a monorepo"
  type        = string
}

variable "repository" {
  description = "Name of the repository to associate with the stack"
  type        = string
}

variable "spacelift_api_key_endpoint" {
  default     = null
  description = "Spacelift API endpoint"
  type        = string
}

variable "spacelift_api_key_id" {
  default     = null
  description = "Spacelift API key ID"
  type        = string
}

variable "spacelift_api_key_secret" {
  default     = null
  description = "Spacelift API key secret"
  type        = string
}

variable "stack_description" {
  default     = null
  description = "Description for the stack"
  type        = string
}

variable "stack_name" {
  description = "Name of the manager stack"
  type        = string
}

variable "namespace" {
  description = "VCS Namespace"
  type        = string
}