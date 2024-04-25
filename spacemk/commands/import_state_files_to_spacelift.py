import base64
import logging

import click

from spacemk import load_normalized_data
from spacemk.spacelift import Spacelift


def _create_context(spacelift: Spacelift, space_id: str, token: str):
    mutation = """
mutation CreateContextV2($input: ContextInput!) {
    contextCreateV2(input: $input) {
        id,
        name
    }
}
"""

    script = """
#!/bin/bash
set -euo pipefail

if [[ -z $TF_TOKEN ]]; then
  echo "TF_TOKEN is not set"
  exit 1
fi

TF_WORKSPACE_ID=$1

echo 'Downloading Terraform state file'
STATE_DOWNLOAD_URL=$(curl --fail \
  --header "Authorization: Bearer $TF_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  --location \
  --show-error \
  --silent \
  "https://app.terraform.io/api/v2/workspaces/${TF_WORKSPACE_ID}/current-state-version" \
  | jq -r '.data.attributes."hosted-state-download-url"' )

echo 'Pushing Terraform state file'
curl --fail \
    --header "Authorization: Bearer $TF_TOKEN" \
    --location \
    --output state.tfstate \
    --show-error \
    --silent \
    "${STATE_DOWNLOAD_URL}"
terraform state push -force state.tfstate
"""

    variables = {
        "input": {
            "description": "",
            "labels": ["autoattach:*"],
            "name": f"SMK Terraform Token-{space_id}",
            "space": space_id,
            "stackAttachments": [],
            "configAttachments": [
                {
                    "description": "",
                    "id": "TF_TOKEN",
                    "type": "ENVIRONMENT_VARIABLE",
                    "value": token,
                    "writeOnly": True,
                },
                {
                    "description": "",
                    "id": "import-state-from-tf.sh",
                    "type": "FILE_MOUNT",
                    "value": base64.b64encode(script.encode()).decode(),
                    "writeOnly": False,
                },
            ],
            "hooks": {
                "beforeInit": [],
                "afterInit": [],
                "beforePlan": [],
                "afterPlan": [],
                "beforeApply": [],
                "afterApply": [],
                "beforeDestroy": [],
                "afterDestroy": [],
                "beforePerform": [],
                "afterPerform": [],
                "afterRun": [],
            },
        }
    }

    logging.info(f"Creating context for space '{space_id}'")
    spacelift.call_api(operation=mutation, variables=variables)


def _delete_context(spacelift: Spacelift, space_id: str):
    context_id = f"smk-terraform-token-{space_id.lower()}"

    logging.info(f"Deleting context for space '{space_id}'")

    update_context_mutation = """
mutation UpdateContext($id: ID!, $name: String!, $description: String, $labels: [String!], $space: ID) {
  contextUpdateV2(
    id: $id
    input: {name: $name, description: $description, labels: $labels, space: $space}
  ) {
    id
    name
    __typename
  }
}
"""
    update_context_variables = {
        "id": context_id,
        "name": f"SMK Terraform Token-{space_id}",
        "description": "",
        "space": space_id,
        "labels": [],  # Remove the autoattach label
    }
    spacelift.call_api(operation=update_context_mutation, variables=update_context_variables)

    delete_context_mutation = """
mutation DeleteContextForContextList($id: ID!) {
  contextDelete(id: $id) {
    id
  }
}
"""
    delete_context_variables = {"id": context_id}
    spacelift.call_api(operation=delete_context_mutation, variables=delete_context_variables)


def _get_space_ids(spacelift: Spacelift) -> list:
    query = """
query GetSpaces {
  spaces {
    id
  }
}
"""

    response = spacelift.call_api(operation=query)

    return [space.id for space in response.get("data.spaces")]


def _trigger_task(spacelift: Spacelift, stack_id: str, workspace_id: str) -> None:
    logging.info(f"Triggering task for stack '{stack_id}'")

    command = f"/mnt/workspace/import-state-from-tf.sh '{workspace_id}'"
    spacelift.trigger_task(stack_id=stack_id, command=command, wait=True)


@click.command(help="Upload Terraform state files to Spacelift.")
@click.decorators.pass_meta_key("config")
def import_state_files_to_spacelift(config):
    data = load_normalized_data()
    spacelift = Spacelift(config.get("spacelift"))
    space_ids = _get_space_ids(spacelift=spacelift)

    for space_id in space_ids:
        # Create a Context with the TFC/TFE token that auto-attaches to all stacks
        _create_context(spacelift=spacelift, space_id=space_id, token=config.exporter.settings.api_token)

    for stack in data.get("stacks"):
        stack_id = stack.slug
        workspace_id = stack._source_id  # noqa: SLF001

        # Trigger a run that pulls the state file from TFC/TFE and pushes it to Spacelift
        _trigger_task(spacelift=spacelift, stack_id=stack_id, workspace_id=workspace_id)

    for space_id in space_ids:
        # Delete the Context with the TFC/TFE token that auto-attaches to all stacks
        _delete_context(spacelift=spacelift, space_id=space_id)
