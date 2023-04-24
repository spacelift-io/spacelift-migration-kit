# Terraform Cloud/Enterprise organization name
tfc_organization = "{{.Tfc_organization}}"

# Export Terraform state to files?
export_state = {{.Export_state}}

# Terraform Cloud/Enterprise does not return the VCS provider name so we use the value below instead.
vcs_provider = "{{.Vcs_provider}}"

# The name of the entity containing the repository.
# The value should be empty for GitHub.com, the user/organization for GitHub (custom application),
# the project for Bitbucket, and the namespace for Gitlab.
vcs_namespace = "{{.Vcs_namespace}}"

# When the branch for the stack is the repository's default branch,
# the value is empty so we use the value provided below instead
vcs_default_branch = "{{.Vcs_default_branch}}"
