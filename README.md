# Spacelift Migration Kit

## Installation

- Ensure that Python is installed.
- Download the Migration Kit: `git clone git@github.com:spacelift-io/spacelift-migration-kit.git` (or other available
  method in GitHub).
- Go to the Migration Kit folder: `spacelift-migration-kit`.
- Install the Python dependencies: `pip install --requirement requirements.txt`.
- Install the `spacemk` command: `pip install --editable .`.

## Usage

### Configuration

Copy the `config.yml.example` file to `config.yml` and edit it as needed.

Environment variables can be referenced by their name preceded by the `$` sign (e.g., `$API_TOKEN`).
This is helpful if you do not want to store sensitive information in the configuration file.

### Audit

This step is optional but recommended. It will analyze your current setup, and display statistics in the terminal. Also, an Excel file with the list of entities to be migrated is created (`tmp/report.xlsx`).

Additionally, it will perform checks and warn you of possible problems. For example, entities can cannot be
automatically migrated and might need to be handled manually.

### Migration

The migration is split in a few different steps that need to be run in order.

### Export

The `spacemk export` command exports information about the source provider entities and stores them as a normalized JSON file (`tmp/data.json`).

That file can be reviewed and modified before moving to the next step.

### Generate

The `spacemk generate` command uses the normalized JSON file from the export step and uses a [Jinja template](https://jinja.palletsprojects.com/) to generate Terraform code that uses the [Spacelift provider](https://registry.terraform.io/providers/spacelift-io/spacelift/latest/docs) to create Spacelift entities that mimic the behavior of the source provider entities.

Feel free to review and edit the generated code as needed.

### Publish

Once the Terraform code has been generated, push it to a git repository of your choosing that is available to your Spacelift account.

### Deploy

After pushing the generated Terraform has been pushed to a git repository, create a manager stack in Spacelift.

Make it point to the repository, and possibly fodler, where you stored the Terraform code, and make sure to **mark is as administrative**.

Finally, trigger a run to create the Spacelift entities.

### Cleanup

All temporary local artifacts are stored in the `tmp` folder. Delete some or all of it to clean up.

Additionally, you can destroy the Spacelift resources created by the manager stack, and then the manager stack to fully remove the migration artifacts.

**The source vendor setup is left untouched by the Migration Kit** and can be deleted once the migration
has been verified to be successful.

## Uninstallation

- Uninstall the `spacemk` command: `pip uninstall --yes spacemk`.
- Uninstall the Python dependencies: `pip uninstall --requirement requirements.txt --yes`.
- Delete the `spacelift-migration-kit` folder.
