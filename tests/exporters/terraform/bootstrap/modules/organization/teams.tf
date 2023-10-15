resource "tfe_team" "team_1" {
  count = var.tf_edition == "tfc_free" ? 0 : 1

  name         = "smk-team-1"
  organization = tfe_organization.organization.name
  visibility   = "organization"
}

resource "tfe_team" "team_2" {
  count = var.tf_edition == "tfc_free" ? 0 : 1

  name         = "smk-team-2"
  organization = tfe_organization.organization.name
  visibility   = "secret"
}
