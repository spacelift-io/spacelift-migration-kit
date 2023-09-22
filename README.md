# Spacelift Migration Kit


## Installation

- Ensure that Python is installed.
- Download the Migration Kit: `git clone git@github.com:spacelift-io/spacelift-migration-kit.git` (or other available method in GitHub).
- Go to the Migration Kit folder: `spacelift-migration-kit`.
- Install Python dependencies: `pip install -r requirements.txt`.

## Usage

### Configuration

Run the `./migration-kit config` command and answer the questions. The configuration will be generated and saved as `config.yml`, unless a different name and path are provided.

Alternatively, the configuration file can be created manually.

Environment variables can be referenced by their name preceded by the `$` sign (e.g., `$API_TOKEN`). This is helpful if you do not want to store sentive information in the configuration file.

### Audit

This step is optional but recommended. It will analyze your current setup, and display statistics and create an inventory of the entities to be migrated.

Additionally, it will perform checks and warn you of possible problems. For example, entitites can cannot be automatically migrated and might need to be handled manually.

### Migration

The `./migration-kit migrate` command will perform the steps required to migrate, pausing when necessary so that you can review and possibly edit the result of the previous step.

The process can be stopped after any step and can be resumed from there or from the beggining. If restarting from the beginning, temporary files will be deleted. The previous step can be re-run before moving on to the next one.

Please note that if the Terraform state backend changes, the `backend` blocks in the Terraform code for the infrastructure will need to be updated to use the new state backend.

### Cleanup

The `./migration-kit clean` command will try its best to delete the migrated resources so that the migration can be performed again. There is no guarantee that it will be able to perform a full cleanup and manual actrions might be necessary.

**The source vendor setup is left untouched by the Migration Kit** and can be deleted once the migration has been verified to be successful.

## Uninstallation

- Delete the `spacelift-migration-kit` folder.
- Uninstall Python dependencies: `pip uninstall -r requirements.txt`.
