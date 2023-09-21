# Spacelift Migration Kit


## Installation

### Using Python

- Ensure that Python is installed.
- Download the Migration Kit: `git clone git@github.com:spacelift-io/spacelift-migration-kit.git` (or other available method in GitHub).
- Go to the Migration Kit folder: `spacelift-migration-kit`.
- Install Python dependencies: `pip install -r requirements.txt`.

## Using Docker

- Ensure that Docker is installed.
- When running the commands below, replace `./migration-kit` with `docker compose run`. The Docker image will downloaded automatically if not present locally.

Example:
```shell
docker compose run migrate
```

## Usage

The `./migration-kit migrate` command will run all the command below in order, pausing when indicated so that the user can review and possibly edit the result of the previous step. The process can be stopped after any step and can be resumed from there or from the beggining. If restarting from the beginning, temporary files will be deleted. The previous step can be re-run before moving on to the next one.

Please note that if the Terraform state backend changes, the `backend` blocks in the Terraform code for the infrastructure will need to be updated to use the new state backend.

The `./migration-kit clean` command will try its best to delete the migrated resources so that the migration can be performed again. There is no guarantee that it will be able to perform a full cleanup.

The source vendor setup is left untouched by the Migration Kit and can be deleted once the migration has been verified to be successful.

- If no configuration is specified:
  - And `config.yml` does not exist, runs `./migration-kit config`.
  - And `config.yml` exist, asks whether to use it or create a new one by running `./migration-kit config`.
- `./migration-kit config` (optional)
  - Asks questions to gather settings and secrets. Alternatively, secrets can be passed as environment variables.
  - Generates the `config.yml` configuration file.
- `./migration-kit audit` (optional, can be run independently as long as there is valid `source` section in the `config.yml` file)
  - Asks whether to perform an audit.
  - Inspects the source vendor setup.
  - Displays stats about entities to be migrated.
  - Warns of any foreseen issue with the migration.
- `./migration-kit export`
  - Retrieves data from the source vendor.
  - Maps the source vendor entities to the Spacelift equivalent.
  - Generates the `tmp/data.json` file.
- Pause to allow manual review and possibly editing of the exported data.
- `./migration-kit generate`
  - Generates Terraform code for Spacelift resources based on the exported data.
- Pause to allow manual review and possibly editing of the generated Terraform code.
- Manual Step: Push the generated Terraform code to a git repository.
- `./migration-kit upload-state-files` (optional)
  - Uploads the state files to a Terraform state backend, if Spacelift is not the state backend.
- `./migration-kit import`
  - Creates/updates the manager stack in Spacelift.
  - Triggers the manager stack to create Spacelift resources.
  - Uploads the state files to Spacelift, if Spacelift is the Terraform state backend.

## Uninstallation

### Python

- Delete the `spacelift-migration-kit` folder.
- Uninstall Python dependencies: `pip uninstall -r requirements.txt`.

### Docker

```shell
docker compose down --rmi local
```

## Brain Dump

- Extract -> Reused for the audit script, with the ability to not pull some properties such as variable values (Must be implemented as a function by each exporter)
- Transform -> Map raw data to Spacelift entities, possibly transforming them )Optional, if present in the exporter it will be called otherwise, the step will be skipped)
- Load -> Saves to a JSON file (should be centralized)
- Should we drop support for Docker? If we embed the source code in there, it cannot be tweaked easily and if we don't there is little value in providing a Docker container.

## TODO

- Flag Sentinel policies as an action item
