resource "tfe_variable" "variable_set_1_env_var" {
  category        = "env"
  description     = "Simple environment variable"
  hcl             = false
  key             = "env_var"
  sensitive       = false
  value           = "bar"
  variable_set_id = tfe_variable_set.variable_set_1.id
}

resource "tfe_variable" "variable_set_1_sensitive_env_var" {
  category        = "env"
  description     = "Sensitive environment variable"
  hcl             = false
  key             = "variable_set_1_sensitive_env_var"
  sensitive       = true
  value           = "secret"
  variable_set_id = tfe_variable_set.variable_set_1.id
}

resource "tfe_variable" "variable_set_2_hcl_env_var" {
  category        = "env"
  description     = "HCL environment variable"
  hcl             = true
  key             = "variable_set_2_hcl_env_var"
  sensitive       = false
  value           = "['A', 'B', 'C']"
  variable_set_id = tfe_variable_set.variable_set_2.id
}

resource "tfe_variable" "variable_set_3_sensitive_hcl_env_var" {
  category        = "env"
  description     = "HCL environment variable"
  hcl             = true
  key             = "variable_set_3_sensitive_hcl_env_var"
  sensitive       = true
  value           = "{ bar = 'baz' }"
  variable_set_id = tfe_variable_set.variable_set_3.id
}

resource "tfe_variable" "workspace_1_env_var" {
  category     = "env"
  description  = "Simple environment variable"
  hcl          = false
  key          = "env_var"
  sensitive    = false
  value        = "foo"
  workspace_id = tfe_workspace.workspace_1.id
}

resource "tfe_variable" "workspace_sensitive_env_var" {
  category     = "env"
  description  = "Sensitive environment variable"
  hcl          = false
  key          = "sensitive_env_var"
  sensitive    = true
  value        = "secret"
  workspace_id = tfe_workspace.workspace_1.id
}

resource "tfe_variable" "workspace_hcl_env_var" {
  category     = "env"
  description  = "HCL environment variable"
  hcl          = true
  key          = "hcl_env_var"
  sensitive    = false
  value        = "[1, 2, 3, 4]"
  workspace_id = tfe_workspace.workspace_1.id
}

resource "tfe_variable" "workspace_sensitive_hcl_env_var" {
  category     = "env"
  description  = "HCL environment variable"
  hcl          = true
  key          = "sensitive_hcl_env_var"
  sensitive    = true
  value        = "{ foo = 'secret' }"
  workspace_id = tfe_workspace.workspace_1.id
}
