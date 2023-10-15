resource "tfe_project" "project_1" {
  name         = "smk-project-1"
  organization = tfe_organization.organization.name
}

resource "tfe_project" "project_2" {
  name         = "smk-project-2"
  organization = tfe_organization.organization.name
}
