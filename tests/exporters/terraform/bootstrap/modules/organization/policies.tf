resource "tfe_policy" "opa_1" {
  count = var.policy_type == "opa" ? 1 : 0

  description  = "SMK OPA policy #1"
  enforce_mode = "advisory"
  kind         = "opa"
  name         = "smk-opa-policy-1"
  organization = tfe_organization.organization.name
  policy       = "package example rule[\"not allowed\"] { false }"
  query        = "data.example.rule"
}

resource "tfe_policy" "opa_2" {
  count = var.policy_type == "opa" ? 1 : 0

  description  = "SMK OPA policy #2"
  enforce_mode = "mandatory"
  kind         = "opa"
  name         = "smk-opa-policy-2"
  organization = tfe_organization.organization.name
  policy       = "package example rule[\"not allowed\"] { false }"
  query        = "data.example.rule"
}

resource "tfe_policy" "sentinel_1" {
  count = var.policy_type == "sentinel" ? 1 : 0

  description  = "SMK Sentinel policy #1"
  enforce_mode = "advisory"
  kind         = "sentinel"
  name         = "smk-sentinel-policy-1"
  organization = tfe_organization.organization.name
  policy       = "main = rule { true }"
}

resource "tfe_policy" "sentinel_2" {
  count = var.policy_type == "sentinel" ? 1 : 0

  description  = "SMK Sentinel policy #2"
  enforce_mode = "${var.policy_sentinel_mandatory_enforcement}-mandatory"
  kind         = "sentinel"
  name         = "smk-sentinel-policy-2"
  organization = tfe_organization.organization.name
  policy       = "main = rule { true }"
}
