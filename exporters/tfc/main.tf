locals {
  stack_ids   = [for i, v in data.tfe_workspace_ids.all.ids : v]
  stack_names = [for i, v in data.tfe_workspace_ids.all.ids : i]
  stacks = [for i, v in data.tfe_workspace_ids.all.ids : {
    autodeploy = data.tfe_workspace.all[i].auto_apply
    env_vars = [for i, v in data.tfe_variables.all[v].variables : {
      hcl       = v.hcl
      name      = v.category == "terraform" ? "TF_VAR_${v.name}" : v.name
      sensitive = v.sensitive
      value     = v.value
    }]
    labels            = data.tfe_workspace.all[i].tag_names
    manage_state      = var.export_state
    name              = data.tfe_workspace.all[i].name
    terraform_version = data.tfe_workspace.all[i].terraform_version
    vcs = {
      # The "identifier" argument contains the acccount/organization and the respository names, separated by a slash
      account = length(data.tfe_workspace.all[i].vcs_repo) > 0 ? split("/", data.tfe_workspace.all[i].vcs_repo[0].identifier)[1] : ""

      # When the branch for the stack is the repository's default branch, the value is empty so we use the value provided via the variable
      branch = length(data.tfe_workspace.all[i].vcs_repo) > 0 ? data.tfe_workspace.all[i].vcs_repo[0].branch != "" ? data.tfe_workspace.all[i].vcs_repo[0].branch : var.vcs_default_branch : var.vcs_default_branch

      namespace    = var.vcs_namespace
      project_root = data.tfe_workspace.all[i].working_directory

      # TFC/TFE does not return the VCS provider name so we use the value provided via the variable
      provider = var.vcs_provider

      # The "identifier" argument contains the acccount/organization and the respository names, separated by a slash
      repository = length(data.tfe_workspace.all[i].vcs_repo) > 0 ? split("/", data.tfe_workspace.all[i].vcs_repo[0].identifier)[1] : ""
    }
  }]
  data = jsonencode({
    "stacks" : local.stacks
  })
}

data "tfe_workspace_ids" "all" {
  names        = ["*"]
  organization = var.tfc_organization
}

data "tfe_workspace" "all" {
  for_each = toset(local.stack_names)

  name         = each.key
  organization = var.tfc_organization
}

data "tfe_variables" "all" {
  for_each = toset(local.stack_ids)

  workspace_id = each.key
}

resource "local_file" "data" {
  content  = local.data
  filename = "${path.module}/../../out/data.json"
}

resource "local_file" "generate_temp_tf_files" {
  for_each = var.export_state ? toset(local.stack_names) : []

  content  = templatefile("${path.module}/main.tftpl", { tfc_organization = var.tfc_organization, workspace = each.key })
  filename = "${path.module}/../../out/tf-files/${each.key}/main.tf"
}

resource "null_resource" "export_state_files" {
  depends_on = [local_file.generate_temp_tf_files]
  for_each   = var.export_state ? toset(local.stack_names) : []

  provisioner "local-exec" {
    command     = "mkdir -p ../../state-files && rm -rf .terraform .terraform.lock.hcl terraform.tfstate terraform.tfstate.backup && terraform init -input=false && terraform state pull > ../../state-files/'${each.key}.tfstate'"
    working_dir = "${path.module}/../../out/tf-files/${each.key}"
  }
}

resource "null_resource" "delete_temp_tf_files" {
  count      = var.export_state ? 1 : 0
  depends_on = [null_resource.export_state_files]

  provisioner "local-exec" {
    command     = "rm -rf tf-files"
    working_dir = "${path.module}/../../out/"
  }
}
