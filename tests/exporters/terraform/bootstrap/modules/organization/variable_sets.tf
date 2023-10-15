resource "tfe_variable_set" "variable_set_1" {
  description  = "SMK variable set #1"
  name         = "smk-variable-set-1"
  global       = true
  organization = tfe_organization.organization.name
}

resource "tfe_variable_set" "variable_set_2" {
  description  = "SMK variable set #2"
  name         = "smk-variable-set-2"
  organization = tfe_organization.organization.name
}

resource "tfe_workspace_variable_set" "variable_set_2_workspace_1" {
  variable_set_id = tfe_variable_set.variable_set_2.id
  workspace_id    = tfe_workspace.workspace_1.id
}

resource "tfe_variable_set" "variable_set_3" {
  description  = "SMK variable set #3"
  name         = "smk-variable-set-3"
  organization = tfe_organization.organization.name
}

resource "tfe_workspace_variable_set" "variable_set_3_workspace_1" {
  variable_set_id = tfe_variable_set.variable_set_3.id
  workspace_id    = tfe_workspace.workspace_1.id
}

resource "tfe_workspace_variable_set" "variable_set_3_workspace_2" {
  variable_set_id = tfe_variable_set.variable_set_3.id
  workspace_id    = tfe_workspace.workspace_2.id
}
