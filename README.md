# Spacelift Migration Kit

This repository contains scripts to help you move from various vendors to Spacelift.

There is no one-size-fits-all for this kind of migration so this kit aims at doing the heavy lifting and getting you 90% through. You will likely need to slightly tweak the generated Terraform code to fit your specific context.

## Overview

The migration process is as follows:

- Export the definition for your resources at your current vendor.
- Generate the Terraform code to recreate similar resources at Spacelift using the [Terraform provider](https://registry.terraform.io/providers/spacelift-io/spacelift/latest/docs).
- Review and possibly edit the generated Terraform code.
- Commit the Terraform code to a repository.
- Create a manager Spacelift stack that points to the repository with the Terraform code.

## Supported Source

Currently, only Terraform Cloud/Enterprise is supported as a source.

## Prerequisites

- Terraform


## Instructions

### Preparation

Use the `terraform login spacelift.io` command to ensure that Terraform can interact with your Spacelift account.

Depending on the exporter used, you may need additional steps:

- **Terraform Cloud/Enterprise**: Use the `terraform login` command to ensure that Terraform can interact with your Terraform Cloud/Enterprise account.

### Pre-Migration Cleanup

In order to start fresh, clean up files and folders from previous runs.

```shell
rm -rf ./out ./{exporters/tfc,generator,manager-stack}/.terraform ./{exporters/tfc,generator,manager-stack}/.terraform.lock.hcl ./{exporters/tfc,generator,manager-stack}/terraform.tfstate ./{exporters/tfc,generator,manager-stack}/terraform.tfstate.backup
```

### Export the resource definitions and Terraform state

- Choose an exporter and copy the example `.tfvars` file for it into `exporter.tfvars`.
- Edit that file to match your context.
- Run the following commands:

```shell
cd exporters/<EXPORTER>
terraform init
terraform apply -auto-approve -var-file=../../exporter.tfvars
```

A new `out` folder should have been created. The `data.json` files contains the mapping of your vendor resources to the equivalent Spacelift resources, and the `state-files` folder contains the files for the Terraform state of your stacks, if the state export was enabled.

Please note that once exported the Terraform state files can be imported into Spacelift or to any backend supported by Terraform.

### Generate the Terraform code

- If you want to customize the template that generates the Terraform code, run `cp ../../generator/generator.tftpl ../generator.tftpl`, and edit the `generator.tftpl` file at the root of the repository. If present, it will be used automatically.
- Run the following commands:

```shell
cd ../../generator
terraform init
terraform apply -auto-approve -var-file=../out/data.json
```

### Review and edit the generated Terraform code

A `main.tf` should have been generated in the `out` folder. It contains all the Terraform code for your Spacelift resources.

Mapping resources from a vendor to Spacelift resources is not an exact science. There are gaps in functionality and caveats in the mapping process.

Please carefully review the generated Terraform code and make sure that it looks fine. If it does not, repeat the process with a different configuration or edit the Terraform code.

### Commit the Terraform code

When the Terraform code is ready, commit it to a repository.

### Create a manager Spacelift stack

> :warning: **Check out the VCS system integation**
> If you were using https://docs.spacelift.io/integrations/source-control/github#setting-up-the-custom-application
> set a correct `namespace` variable in `manager-stack/terraform.tfvars`
> and uncomment `github_enterpise` block in `manager-stack/main.tf` file.

It is now time to create a Spacelift stack that will point to the commited Terraform code that manages your Spacelift resources.

- Copy the example `manager-stack.example.tfvars` file into `manager-stack.tfvars` .
- Edit that file to match your context.
- Run the following commands:

```shell
cd ../manager-stack
terraform init
terraform apply -auto-approve -var-file=../manager-stack.tfvars
```

After the stack has been created, a tracked run will be triggered automatically. That run will create the defined Spacelift resources.

### Post-Migration Cleanup

Before you can use Spacelift to manage your infrastructure,  you may need to make changes to the Terraform code for your infrastructure, depending on the Terraform state is managed.

If the Terraform state is managed by Spacelift,perform the following actions, otherwise you can skip this section:

- Remove any [backend](https://developer.hashicorp.com/terraform/language/settings/backends/configuration#using-a-backend-block)/[cloud](https://developer.hashicorp.com/terraform/language/settings/terraform-cloud) block from the Terraform code that manages your infrastructure to avoid a conflict with Spacelift's backend.
- Delete the `import_state_file` arguments from the Terraform code that manages your Spacelift resources.
- After the manager stack has successfully run, the mounted Terraform state files are not needed anymore and can be deleted by setting the `import_state` argument to `false` in the `manager-stack.tfvars` file and run `terraform apply -auto-approve -var-file=../manager-stack.tfvars` in the `manager-stack` folder.


## Known Limitations

### State Files Bigger than 2MB

The current implementation uses [mounted files](https://docs.spacelift.io/concepts/configuration/environment#mounted-files) to upload the exported state files to Spacelift. This works well for most state files but mounted files have a file size limit of 2MB so state files bigger than that cannot be imported that way.

This limitation will be removed in an upcoming release but until then, the workaround is to:

- Do not export the state files nor import them into Spacelift with the Migration Kit.
- Set the `TFC_TOKEN` environment variable with a TFC token as the value. It can be set [on the stacks](https://docs.spacelift.io/concepts/configuration/environment#environment-variables) or as [a context](https://docs.spacelift.io/concepts/configuration/context) attached to multiple stacks.
- Mount the following script as a mounted file named `import-tfc-state.sh`:

```shell
#!/bin/bash
set -euo pipefail

if [[ -z $TFC_TOKEN ]]; then
  echo "TFC_TOKEN is not set"
  exit 1
fi

TFC_WORKSPACE_ID=$1

STATE_DOWNLOAD_URL=$(curl -sSL --fail \
  --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  --request GET \
  "https://app.terraform.io/api/v2/workspaces/${TFC_WORKSPACE_ID}/current-state-version" \
  | jq -r '.data.attributes."hosted-state-download-url"' )

curl -sSL --fail -o state.tfstate "${STATE_DOWNLOAD_URL}"
terraform state push -force state.tfstate
```

- Run the following command as [task](https://docs.spacelift.io/concepts/run/task): `/mnt/workspace/import-tfc-state.sh <TFC WORKSPACE ID>`

Please note that the [spacectl](https://github.com/spacelift-io/spacectl) CLI tool can be used to run those tasks which is helpful if you need to import many big state files: `spacectl stack task --id <STACK ID> --tail /mnt/workspace/import-tfc-state.sh <TFC WORKSPACE ID>`

### Terraform Cloud/Enterprise Exporter

- The variable sets are not exposed so they cannot be listed and exported.
- The name of the Version Control System (VCS) provider for a stack is not returned so it has to be set in the exporter configuration file.
- When the branch for the stack is the repository default branch, the value is empty. You can set the value for the default branch in the exporter configuration file, or edit the generated Terraform code.
