# Migration Wrapper

This tool to automate the migration of Terraform state between Terraform Cloud and Spacelift.io. The tool generates a new repository containing the migrated Terraform code, and sets up Spacelift stacks and associated configurations.

## Prerequisites

- Terraform v0.13 or later installed
- Logged in to both Terraform Cloud and Spacelift.io
- Configured the config.yaml file
- Set the following environment variables:
  - TF_VAR_spacelift_api_key_id
  - TF_VAR_spacelift_api_key_secret
  - VCS_Token

## Usage

- Clone this repository and navigate to the root folder.
- Update the config.yaml file with the relevant details for your migration.
- Set the required environment variables.
- Run the script with the appropriate flags. Some available flags are:
  - -login: Run the Terraform login commands for TFC and Spacelift.io.
  - -c: Clean up the generated files and folders for a new migration.
  - -h: Display help information.
  - -migrate: Start a migration.

For example, to start a new migration:

```go
go run main.go -migrate
```

## Troubleshooting

If you encounter any issues during the migration, you can use the -c flag to clean up the generated files and folders, and start a new migration.

```go
go run main.go -c
```
