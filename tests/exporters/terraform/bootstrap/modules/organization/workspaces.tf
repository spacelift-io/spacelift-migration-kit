resource "tfe_oauth_client" "github" {
  count = var.github_oauth_token == null ? 0 : 1

  api_url          = "https://api.github.com"
  name             = "smk-github-oauth-client"
  organization     = tfe_organization.organization.name
  http_url         = "https://github.com"
  oauth_token      = var.github_oauth_token
  service_provider = "github"
}

resource "tfe_workspace" "workspace_1" {
  assessments_enabled = false
  auto_apply          = false
  description         = "SMK Workspace #1"
  execution_mode      = "remote"
  name                = "smk-workspace-1"
  organization        = tfe_organization.organization.name
  project_id          = tfe_project.project_1.id
  speculative_enabled = true
  tag_names           = ["tag-1", "tag-2"]
  terraform_version   = ">= 1.2.0"
}

resource "tfe_workspace" "workspace_2" {
  assessments_enabled = contains(["tfc_plus", "tfe"], var.tf_edition)
  auto_apply          = true
  description         = "SMK Workspace #2"
  execution_mode      = "local"
  name                = "smk-workspace-2"
  organization        = tfe_organization.organization.name
  project_id          = tfe_project.project_2.id
  speculative_enabled = false
  tag_names           = ["tag-1"]
  terraform_version   = "0.12.0"
}

resource "tfe_workspace" "workspace_github_1" {
  count = var.github_oauth_token == null ? 0 : 1

  agent_pool_id       = tfe_agent_pool.agent_pool_1.id
  assessments_enabled = false
  auto_apply          = false
  description         = "SMK Workspace GitHub #1"
  execution_mode      = "agent"
  name                = "smk-workspace-github-1"
  organization        = tfe_organization.organization.name
  project_id          = tfe_project.project_2.id
  speculative_enabled = true
  tag_names           = ["tag-1", "tag-3"]
  terraform_version   = "~> 1.0.0"

  vcs_repo {
    identifier         = "smk/example"
    branch             = "main"
    ingress_submodules = false
    oauth_token_id     = tfe_oauth_client.github[0].oauth_token_id
  }
}

resource "tfe_workspace" "workspace_github_2" {
  count = var.github_oauth_token == null ? 0 : 1

  agent_pool_id       = tfe_agent_pool.agent_pool_1.id
  assessments_enabled = false
  auto_apply          = false
  description         = "SMK Workspace GitHub #2"
  execution_mode      = "agent"
  name                = "smk-workspace-github-2"
  organization        = tfe_organization.organization.name
  project_id          = tfe_project.project_2.id
  speculative_enabled = true
  tag_names           = ["tag-1", "tag-4"]
  terraform_version   = "~> 1.1.0"
  working_directory   = "/path/to/working/another/directory"

  vcs_repo {
    identifier         = "smk/example"
    branch             = "main"
    ingress_submodules = true
    oauth_token_id     = tfe_oauth_client.github[0].oauth_token_id
  }
}
