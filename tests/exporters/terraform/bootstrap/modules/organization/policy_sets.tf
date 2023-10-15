resource "tfe_policy_set" "opa_set_1" {
  count = var.policy_type == "opa" ? 1 : 0

  name          = "smk-opa-policy-set-1"
  description   = "SMK OPA policy set #1"
  kind          = "opa"
  organization  = tfe_organization.organization.name
  policy_ids    = [tfe_policy.opa_1[0].id, tfe_policy.opa_2[0].id]
  workspace_ids = [tfe_workspace.workspace_2.id]
}

resource "tfe_policy_set" "sentinel_set_1" {
  count = var.policy_type == "sentinel" ? 1 : 0

  name          = "smk-sentinel-policy-set-1"
  description   = "SMK Sentinel policy set #1"
  kind          = "sentinel"
  organization  = tfe_organization.organization.name
  policy_ids    = [tfe_policy.sentinel_1[0].id, tfe_policy.sentinel_2[0].id]
  workspace_ids = [tfe_workspace.workspace_2.id]
}
