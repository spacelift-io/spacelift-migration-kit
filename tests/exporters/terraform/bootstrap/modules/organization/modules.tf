resource "tfe_registry_module" "private_registry" {
  module_provider = "smk"
  name            = "example_module"
  organization    = tfe_organization.organization.name
  registry_name   = "private"
}

resource "tfe_registry_module" "public_registry" {
  module_provider = "aws"
  name            = "vpc"
  namespace       = "terraform-aws-modules"
  organization    = tfe_organization.organization.name
  registry_name   = "public"
}
