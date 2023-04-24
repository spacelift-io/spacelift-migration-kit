terraform {
  required_version = "~> 1.2"

  required_providers {
    spacelift = {
      source  = "spacelift-io/spacelift"
      version = "~> 0.1"
    }
  }
}

provider "spacelift" {
  api_key_endpoint = var.spacelift_api_key_endpoint
  api_key_id       = var.spacelift_api_key_id
  api_key_secret   = var.spacelift_api_key_secret
}

locals {
  # This allows to export the state from the source but not import it into Spacelift
  # by working around Terraform not accepting to define both "count" and "for_each"
  state_files = var.import_state ? fileset("../out/state-files", "*.tfstate") : []
}

resource "spacelift_stack" "manager" {
  administrative = true
  branch         = var.branch
  description    = var.stack_description
  name           = var.stack_name
  project_root   = var.project_root

  dynamic "github_enterprise" {
    for_each = var.vcs_provider == "github_enterprise" ? [1] : []
    content {
      namespace = var.vcs_namespace
    }
  }

  dynamic "bitbucket_cloud" {
    for_each = var.vcs_provider == "bitbucket_cloud" ? [1] : []
    content {
      namespace = var.vcs_namespace
    }
  }

  dynamic "bitbucket_datacenter" {
    for_each = var.vcs_provider == "bitbucket_datacenter" ? [1] : []
    content {
      namespace = var.vcs_namespace
    }
  }

  dynamic "gitlab" {
    for_each = var.vcs_provider == "gitlab" ? [1] : []

    content {
      namespace = var.vcs_namespace
    }
  }

  dynamic "azure_devops" {
    for_each = var.vcs_provider == "azure_devops" ? [1] : []
    content {
      project = var.vcs_namespace
    }
  }

  repository = var.repository
}

resource "spacelift_run" "manager" {
  stack_id = spacelift_stack.manager.id

  keepers = {
    # Trigger a run when "import_state" variable changes to facilitate
    # the deletion of the mounted files after the stacks have been created
    branch = var.import_state
  }
}

resource "spacelift_mounted_file" "state_file" {
  for_each = local.state_files

  content       = filebase64("../out/state-files/${each.value}")
  relative_path = "state-import/${each.value}"
  stack_id      = spacelift_stack.manager.id
}
