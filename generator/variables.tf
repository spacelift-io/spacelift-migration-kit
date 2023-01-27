variable "stacks" {
  description = "Stacks to import"
  type = list(object({
    autodeploy = bool
    env_vars = list(object({
      hcl       = bool
      name      = string
      sensitive = bool
      value     = string
    }))
    manage_state      = bool
    name              = string
    terraform_version = string
    vcs = object({
      account      = string
      branch       = string
      namespace    = string
      project_root = string
      provider     = string
      repository   = string
    })
  }))
}
