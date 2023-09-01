# Spacelift Migration Kit

## Steps

All steps are automated unless specified.

- Generate configuration file manually or via the `config` command.
- Check pre-requisites.
  - Source vendor API token.
  - Spacelift admin API token.
- Export data from the source vendor.
- Review and possibly edit the exported data (optional, manual).
- Generate Terraform code for Spacelift resources based on the exported data.
- Review and possibly edit the generated code (optional, manual).
- Push the generated code to a git repository (manual).
- Create/update the manager stack in Spacelift.
- Trigger the manager stack to create resources.
- Upload the state files if needed.
