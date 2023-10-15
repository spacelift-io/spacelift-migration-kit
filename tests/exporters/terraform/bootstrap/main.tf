module "organization_1" {
  source = "./modules/organization"

  github_oauth_token = var.github_oauth_token
  name               = "smk-organization-1"
  policy_type        = "opa"
  tf_edition         = var.tf_edition
}

module "organization_2" {
  source = "./modules/organization"

  github_oauth_token                    = var.github_oauth_token
  name                                  = "smk-organization-2"
  policy_sentinel_mandatory_enforcement = "hard"
  policy_type                           = "sentinel"
  tf_edition                            = var.tf_edition
}

module "organization_3" {
  source = "./modules/organization"

  github_oauth_token                    = var.github_oauth_token
  name                                  = "smk-organization-3"
  policy_sentinel_mandatory_enforcement = "soft"
  policy_type                           = "sentinel"
  tf_edition                            = var.tf_edition
}
