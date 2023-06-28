# Terraform Cloud/Enterprise organization name
tfc_organization = ""

# List of TFC/TFE workspace names to export. Wildcards are supported (e.g., ["*"], ["*-example"], ["example-*"]).
# tfc_workspace_names = ["*"]

# List of TFC/TFE workspace tags to include when exporting. Excluded tags take precedence over included ones. Wildcards are not supported.
# tfc_workspace_include_tags = ["example"]

# List of TFC/TFE workspace tags to exclude when exporting. Excluded tags take precedence over included ones. Wildcards are not supported.
# tfc_workspace_exclude_tags = ["ignore"]

# Export Terraform state to files?
export_state = true

# Terraform Cloud/Enterprise does not return the VCS provider name so we use the value below instead.
vcs_provider = "github"

# The name of the entity containing the repository.
# The value should be empty for GitHub.com, the user/organization for GitHub (custom application),
# the project for Bitbucket, and the namespace for Gitlab.
vcs_namespace = ""

# When the branch for the stack is the repository's default branch,
# the value is empty so we use the value provided below instead
vcs_default_branch = "main"
