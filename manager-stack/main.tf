terraform {
  required_version = "~> 1.2"

  required_providers {
    spacelift = {
      source  = "spacelift-io/spacelift"
      version = "~> 1.0"
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
  repository     = var.repository
  # If you are using GitHub custom app installation https://docs.spacelift.io/integrations/source-control/github#setting-up-the-custom-application
  # uncomment the following lines
  # github_enterprise {
  #   namespace = var.namespace
  # }
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
