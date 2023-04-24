# Name of the manager stack
stack_name = "{{.Stack_name}}"

# Description for the stack
stack_description = "{{.Stack_description}}"

# Name of the repository to associate with the stack
repository = "{{.Repository}}"

# Name of the branch to associate with the stack
branch = "{{.Branch}}"

# Path to the folder containing the Terraform code, in case of a monorepo
project_root = "{{.Project_root}}"

# Import the Terraform state for the managed stacks into Spacelift?
import_state = {{.Import_state}}

# Spacelift API endpoint
spacelift_api_key_endpoint = "{{.Spacelift_api_key_endpoint}}"

vcs_provider = "{{.VCS_provider}}"
 
vcs_namespace = "{{.VCS_namespace}}"