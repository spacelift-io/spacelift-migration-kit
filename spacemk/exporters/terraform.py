# ruff: noqa: PERF401
import json
import logging
import re
import time
from http import HTTPStatus
from pathlib import Path

import click
import pydash
import requests
from benedict import benedict
from python_on_whales import Container, docker
from requests_toolbelt.utils import dump as request_dump
from slugify import slugify

from spacemk import get_tmp_subfolder, is_command_available
from spacemk.exporters import BaseExporter


class TerraformExporter(BaseExporter):
    def __init__(self, config: dict):
        super().__init__(config)

        self._property_mapping = {
            "organizations": {
                "attributes.email": "properties.email",
                "attributes.name": "properties.name",
                "id": "properties.id",
            }
        }

    def _build_stack_slug(self, workspace: dict) -> str:
        return slugify(workspace.get("attributes.name"))

    def _call_api(
        self,
        url: str,
        drop_response_properties: list | None = None,
        method: str = "GET",
        request_data: dict | None = None,
    ) -> dict:
        logging.info("Start calling API")

        headers = {
            "Authorization": f"Bearer {self._config.get('api_token')}",
            "Content-Type": "application/vnd.api+json",
        }

        try:
            if request_data is not None:
                request_data = json.dumps(request_data)

            response = requests.request(data=request_data, headers=headers, method=method, url=url)
            logging.debug(request_dump.dump_all(response).decode("utf-8"))
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            # Return None for non-existent API endpoints as we are most likely interacting with an older TFE version
            if e.response.status_code == HTTPStatus.NOT_FOUND:
                logging.warning(f"Non-existent API endpoint ({url}). Ignoring.")
                return {"data": {}}

            raise RuntimeError(f"HTTP Error: {e}") from e
        except requests.exceptions.ReadTimeout as e:
            raise RuntimeError(f"Timeout for {url}") from e
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(f"Connection error for {url}") from e
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error for {url}") from e

        if drop_response_properties:
            # Drop properties, mostly when they contain the keypath separator benedict uses (ie ".")
            data = benedict(pydash.omit(response.json(), drop_response_properties))
        elif len(response.content) == 0:
            # The response has no content (e.g. 204 HTTP status code)
            data = benedict()
        else:
            data = benedict(response.json())

        logging.info("Stop calling API")

        return data

    def _check_data(self, data: list[dict]) -> list[dict]:
        logging.info("Start checking data")

        data["agent_pools"] = self._check_agent_pools_data(data.get("agent_pools"))
        data["modules"] = self._check_modules_data(data.get("modules"))
        data["policies"] = self._check_policies_data(data.get("policies"))
        data["workspaces"] = self._check_workspaces_data(data.get("workspaces"))
        data["workspace_variables"] = self._check_workspace_variables_data(data.get("workspace_variables"))

        logging.info("Stop checking data")

        return data

    def _check_agent_pools_data(self, data: list[dict]) -> list[dict]:
        logging.info("Start checking agent pools data")

        for key, item in enumerate(data):
            warnings = []

            if item.get("attributes.agent-count") == 0:
                warnings.append("No agents")

            data[key]["warnings"] = ", ".join(warnings)

        logging.info("Stop checking agent pools data")

        return data

    def _check_modules_data(self, data: list[dict]) -> list[dict]:
        logging.info("Start checking modules data")

        for key, item in enumerate(data):
            warnings = []

            if item.get("attributes.status") != "setup_complete":
                warnings.append("Setup incomplete")

            data[key]["warnings"] = ", ".join(warnings)

        logging.info("Stop checking modules data")

        return data

    def _check_policies_data(self, data: list[dict]) -> list[dict]:
        logging.info("Start checking policies data")

        for key, item in enumerate(data):
            warnings = []

            # Older Terraform Enterprise versions only supported Sentinel policies
            if not item.get("attributes.kind") or item.get("attributes.kind") == "sentinel":
                warnings.append("Sentinel policy")

            data[key]["warnings"] = ", ".join(warnings)

        logging.info("Stop checking policies data")

        return data

    def _check_requirements(self, action: str) -> None:  # noqa: ARG002
        """Check if the exporter requirements are met"""
        logging.info("Start checking requirements")

        if not is_command_available(["docker", "ps"], execute=True):
            logging.warning("Docker is not available. Sensitive variables will not be retrieved.")

            click.confirm("Do you want to continue?", abort=True)

        logging.info("Stop checking requirements")

    def _check_workspace_variables_data(self, data: list[dict]) -> list[dict]:
        logging.info("Start checking workspace variables data")

        prog = re.compile("^[a-zA-Z_]+[a-zA-Z0-9_]*$")
        for key, item in enumerate(data):
            warnings = []

            if not re.search(prog, item.get("attributes.key")):
                warnings.append("Key is an invalid env var name")

            data[key]["warnings"] = ", ".join(warnings)

        logging.info("Stop checking workspace variables data")

        return data

    def _check_workspaces_data(self, data: list[dict]) -> list[dict]:
        logging.info("Start checking workspaces data")

        for key, item in enumerate(data):
            warnings = []

            if item.get("attributes.resource-count") == 0:
                warnings.append("No resources")

            if item.get("attributes.vcs-repo.service-provider") is None:
                warnings.append("No VCS configuration")

            data[key]["warnings"] = ", ".join(warnings)

        logging.info("Stop checking workspaces data")

        return data

    def _create_agent_pool(self, organization_id: str) -> str:
        agent_pool_request_data = {
            "data": {
                "attributes": {
                    "name": "SMK",
                    "organization-scoped": True,
                },
                "type": "agent-pools",
            }
        }
        agent_pool_data = self._extract_data_from_api(
            method="POST",
            path=f"/organizations/{organization_id}/agent-pools",
            properties=["id"],
            request_data=agent_pool_request_data,
        )
        agent_pool_id = agent_pool_data[0].get("id")
        logging.info(f"Created '{agent_pool_id}' agent pool")

        return agent_pool_id

    def _create_agent_token(self, agent_pool_id: str) -> str:
        agent_token_request_data = {
            "data": {
                "attributes": {
                    "description": "SMK",
                },
                "type": "authentication-tokens",
            }
        }
        agent_token_data = self._extract_data_from_api(
            method="POST",
            path=f"/agent-pools/{agent_pool_id}/authentication-tokens",
            properties=["attributes.token", "id"],
            request_data=agent_token_request_data,
        )
        agent_token_id = agent_token_data[0].get("id")
        agent_token = agent_token_data[0].get("attributes.token")

        logging.info(f"Created '{agent_token_id}' agent token")

        return agent_token

    def _delete_agent_pool(self, id_: str) -> None:
        logging.info(f"Deleting '{id_}' agent pool")
        self._extract_data_from_api(
            method="DELETE",
            path=f"/agent-pools/{id_}",
        )

    def _download_text_file(self, url: str) -> str:
        logging.info("Start downloading text file")

        headers = {
            "Authorization": f"Bearer {self._config.get('api_token')}",
        }
        response = requests.get(allow_redirects=True, headers=headers, url=url)
        logging.debug(request_dump.dump_all(response).decode("utf-8"))

        logging.info("Stop downloading text file")

        return response.text

    def _download_state_files(self, data: dict) -> None:
        logging.info("Start downloading state files")

        for workspace in data.get("workspaces"):
            state_version_id = workspace.get("relationships.current-state-version.data.id")
            if state_version_id:
                state_version_data = self._extract_data_from_api(
                    drop_response_properties=[
                        "data.attributes.modules",
                        "data.attributes.providers",
                        "data.attributes.resources",
                    ],
                    path=f"/state-versions/{state_version_id}",
                    properties=["attributes.hosted-state-download-url"],
                )

                state_file_content = self._download_text_file(
                    url=state_version_data[0].get("attributes.hosted-state-download-url")
                )

                # KLUDGE: The Terraform API response is returned a "application/octet-stream"
                # and includes encoded unicode characters that need to be decoded before saving the state file
                state_file_content = json.dumps(json.loads(state_file_content), indent=2)

                organization_id = workspace.get("relationships.organization.data.id")
                workspace_id = workspace.get("id")

                path = Path(get_tmp_subfolder(f"state-files/{organization_id}"), f"{workspace_id}.tfstate")
                with path.open("w", encoding="utf-8") as fp:
                    logging.debug(f"Saving state file for '{organization_id}/{workspace_id}' to '{path}'")
                    fp.write(state_file_content)

        logging.info("Stop downloading state files")

    # KLUDGE: We should break this function down in smaller functions
    def _enrich_workspace_variable_data(self, data: dict) -> dict:  # noqa: PLR0912, PLR0915
        def find_workspace(data: dict, workspace_id: str) -> dict:
            for workspace in data.get("workspaces"):
                if workspace.get("id") == workspace_id:
                    return workspace

            logging.warning(f"Could not find workspace '{workspace_id}'")

            return None

        def find_variable(data: dict, variable_id: str) -> dict:
            for variable in data.get("workspace_variables"):
                if variable.get("id") == variable_id:
                    return variable

            logging.warning(f"Could not find variable '{variable_id}'")

            return None

        if not is_command_available(["docker", "ps"], execute=True):
            logging.warning("Docker is not available. Skipping enriching workspace variables data.")
            return data

        logging.info("Start enriching workspace variables data")

        # List organizations, workspaces and associated variables
        organizations = benedict()
        for variable in data.get("workspace_variables"):
            if variable.get("attributes.sensitive") is False:
                continue

            workspace_id = variable.get("relationships.workspace.data.id")
            organization_id = find_workspace(data, workspace_id).get("relationships.organization.data.id")

            if organization_id not in organizations:
                organizations[organization_id] = benedict()

            if workspace_id not in organizations[organization_id]:
                organizations[organization_id][workspace_id] = benedict()

            organizations[organization_id][workspace_id][variable.get("id")] = variable.get("attributes.key")

        if len(organizations) == 0 or len(organizations.keys()) == 0:
            return data

        for organization_id, workspaces in organizations.items():
            logging.info(f"Start local TFC/TFE agent for organization '{organization_id}'")

            agent_pool_id = self._create_agent_pool(organization_id=organization_id)

            try:
                agent_container_name = f"smk-tfc-agent-{organization_id}"
                agent_container = self._start_agent_container(
                    agent_pool_id=agent_pool_id, container_name=agent_container_name
                )

                # Store the container ID in case it gets stopped and we need it for the error message
                agent_container_id = agent_container.id

                for workspace_id, workspace_variables in workspaces.items():
                    current_configuration_version_id = find_workspace(data, workspace_id).get(
                        "relationships.current-configuration-version.data.id"
                    )
                    if current_configuration_version_id is None:
                        logging.warning(
                            f"Workspace '{organization_id}/{workspace_id}' has no current configuration. Ignoring."
                        )
                        continue

                    logging.info(f"Backing up the '{organization_id}/{workspace_id}' workspace execution mode")
                    workspace_data_backup = self._extract_data_from_api(
                        path=f"/workspaces/{workspace_id}",
                        properties=[
                            "attributes.execution-mode",
                            "attributes.setting-overwrites",
                            "relationships.agent-pool",
                        ],
                    )[
                        0
                    ]  # KLUDGE: There should be a way to pull single item from the API instead of a list of items

                    logging.info(f"Updating the '{organization_id}/{workspace_id}' workspace to use the TFC Agent")
                    self._extract_data_from_api(
                        method="PATCH",
                        path=f"/workspaces/{workspace_id}",
                        request_data={
                            "data": {
                                "attributes": {
                                    "agent-pool-id": agent_pool_id,
                                    "execution-mode": "agent",
                                    "setting-overwrites": {"execution-mode": True, "agent-pool": True},
                                },
                                "type": "workspaces",
                            }
                        },
                    )

                    logging.info(f"Trigger a plan for the '{organization_id}/{workspace_id}' workspace")
                    run_data = self._extract_data_from_api(
                        method="POST",
                        path="/runs",
                        properties=["relationships.plan.data.id"],
                        request_data={
                            "data": {
                                "attributes": {
                                    "allow-empty-apply": False,
                                    "plan-only": True,
                                    "refresh": False,  # No need to waste time refreshing the state
                                },
                                "relationships": {
                                    "workspace": {"data": {"id": workspace_id, "type": "workspaces"}},
                                },
                                "type": "runs",
                            }
                        },
                    )[
                        0
                    ]  # KLUDGE: There should be a way to pull single item from the API instead of a list of items

                    logging.info("Retrieve the output for the plan")
                    plan_id = run_data.get("relationships.plan.data.id")
                    plan_data = self._get_plan(id_=plan_id)

                    if plan_data.get("attributes.log-read-url"):
                        logs_data = self._download_text_file(url=plan_data.get("attributes.log-read-url"))

                        logging.debug("Plan output:")
                        logging.debug(logs_data)

                        logging.info("Extract the env var values from the plan output")
                        for line in logs_data.split("\n"):
                            for workspace_variable_id, workspace_variable_name in workspace_variables.items():
                                prefix = f"{workspace_variable_name}="
                                if line.startswith(prefix):
                                    value = line.removeprefix(prefix)
                                    masked_value = "*" * len(value)

                                    logging.debug(
                                        f"Found sensitive env var: '{workspace_variable_name}={masked_value}'"
                                    )

                                    variable = find_variable(data, workspace_variable_id)
                                    variable["attributes.value"] = value

                                # KLUDGE: Ideally this should be retrieved independently for more clarity,
                                # and only if needed.
                                if line.startswith("ATLAS_CONFIGURATION_VERSION_GITHUB_BRANCH="):
                                    branch_name = line.removeprefix("ATLAS_CONFIGURATION_VERSION_GITHUB_BRANCH=")
                                    workspace = find_workspace(data, workspace_id)
                                    if workspace and not workspace.get("attributes.vcs-repo.branch"):
                                        workspace["attributes.vcs-repo.branch"] = branch_name

                    logging.info(f"Restoring the '{organization_id}/{workspace_id}' workspace execution mode")
                    self._extract_data_from_api(
                        method="PATCH",
                        path=f"/workspaces/{workspace_id}",
                        request_data={
                            "data": {
                                "attributes": {
                                    "execution-mode": workspace_data_backup.get("attributes.execution-mode"),
                                    "setting-overwrites": workspace_data_backup.get("attributes.setting-overwrites"),
                                },
                                "relationships": {
                                    "agent-pool": workspace_data_backup.get("relationships.agent-pool"),
                                },
                                "type": "workspaces",
                            }
                        },
                    )

                if agent_container.exists() and agent_container.state.running:
                    logging.debug(f"Local TFC/TFE agent Docker container '{agent_container_id}' logs:")
                    logging.debug(agent_container.logs())
                else:
                    logging.warning(
                        f"Local TFC/TFE agent Docker container '{agent_container_id}' "
                        "was already stopped when we tried to pull the logs. Skipping."
                    )
            finally:
                logging.info(f"Stop local TFC/TFE agent for organization '{organization_id}'")
                self._stop_agent_container(agent_container)

                self._delete_agent_pool(id_=agent_pool_id)

        logging.info("Stop enriching workspace variables data")

        return data

    def _enrich_data(self, data: dict) -> dict:
        logging.info("Start enriching data")

        self._download_state_files(data)
        data = self._enrich_workspace_variable_data(data)

        logging.info("Stop enriching data")

        return data

    def _expand_relationships(self, data: dict) -> dict:
        def find_entity(data: dict, type_: str, id_: str) -> dict:
            # Pluralize the type
            type_ = f"{type_}s"
            for src_datum in data.get(type_):
                if src_datum.get("_source_id") == id_:
                    # Clone to avoid modifying the original dict when removing the relationships
                    # on the expanded relationship
                    datum = src_datum.clone()

                    if "_relationships" in datum:
                        del datum["_relationships"]

                    return datum

            return None

        logging.info("Start expanding relationships")

        for entity_data in data.values():
            for datum in entity_data:
                relationships = {}
                if datum.get("_relationships"):
                    for type_, id_ in datum.get("_relationships").items():
                        relationships[type_] = find_entity(data=data, id_=id_, type_=type_)

                datum.update(
                    {"_migration_id": self._generate_migration_id(datum.get("name")), "_relationships": relationships}
                )

        logging.info("Stop expanding relationships")

        return data

    def _extract_data(self) -> list[dict]:
        logging.info("Start extracting data")
        data = benedict(
            {
                "agent_pools": [],
                "modules": [],
                "organizations": self._extract_organization_data(),
                "policies": [],
                "policy_sets": [],
                "projects": [],
                "providers": [],
                "tasks": [],
                "teams": [],
                "variable_sets": [],
                "workspace_variables": [],
                "workspaces": [],
            }
        )

        for organization in data.organizations:
            data["agent_pools"].extend(self._extract_agent_pools_data(organization))
            data["modules"].extend(self._extract_modules_data(organization))
            data["policies"].extend(self._extract_policies_data(organization))
            data["policy_sets"].extend(self._extract_policy_sets_data(organization))
            data["projects"].extend(self._extract_projects_data(organization))
            data["providers"].extend(self._extract_providers_data(organization))
            data["tasks"].extend(self._extract_tasks_data(organization))
            data["teams"].extend(self._extract_teams_data(organization))
            data["variable_sets"].extend(self._extract_variable_sets_data(organization))
            data["workspaces"].extend(self._extract_workspaces_data(organization))

        for workspace in data.workspaces:
            data["workspace_variables"].extend(self._extract_workspace_variables_data(workspace))

        logging.info("Stop extracting data")

        return data

    def _extract_data_from_api(
        self,
        path: str,
        drop_response_properties: list | None = None,
        include_pattern: str | None = None,
        method: str = "GET",
        properties: list | None = None,
        request_data: dict | None = None,
    ) -> list[dict]:
        logging.info("Start extracting data from API")

        if include_pattern is None:
            include_pattern = ".*"

        endpoint = self._config.get("api_endpoint", "https://app.terraform.io")
        url = f"{endpoint}/api/v2{path}"

        raw_data = []
        while True:
            response_payload = self._call_api(
                url, drop_response_properties=drop_response_properties, method=method, request_data=request_data
            )

            if response_payload.get("data"):
                if isinstance(response_payload["data"], dict):  # Individual resource
                    raw_data.append(response_payload["data"])
                else:  # Collection of resources
                    raw_data.extend(response_payload["data"])

            if response_payload.get("links.next"):
                logging.debug("Pulling the next page from the API")
                url = response_payload.get("links.next")
            else:
                break

        include_regex = re.compile(include_pattern)

        data = []
        for raw_datum in raw_data:
            if raw_datum.get("attributes.name") and include_regex.match(raw_datum.get("attributes.name")) is None:
                continue

            if properties:
                # KLUDGE: There must be a cleaner way to handle this
                datum = benedict()
                for property_ in properties:
                    datum[property_] = raw_datum.get(property_)
                data.append(datum)

        logging.info("Stop extracting data from API")

        return data

    def _extract_agent_pools_data(self, organization: dict) -> list[dict]:
        logging.info("Start extracting agent pools data")

        properties = [
            "attributes.agent-count",
            "attributes.name",
            "attributes.organization-scoped",
            "id",
            "relationships.organization.data.id",
        ]
        data = self._extract_data_from_api(
            include_pattern=self._config.get("include.agent_pools"),
            path=f"/organizations/{organization.get('id')}/agent-pools",
            properties=properties,
        )

        logging.info("Stop extracting agent pools data")

        return data

    def _extract_modules_data(self, organization: dict) -> list[dict]:
        logging.info("Start extracting modules data")

        properties = [
            "attributes.name",
            "attributes.namespace",
            "attributes.provider",
            "attributes.registry-name",
            "id",
        ]
        list_data = self._extract_data_from_api(
            include_pattern=self._config.get("include.modules"),
            path=f"/organizations/{organization.get('id')}/registry-modules",
            properties=properties,
        )

        data = []
        for list_datum in list_data:
            module_data = self._extract_data_from_api(
                path=f"/organizations/{organization.get('id')}/registry-modules/{list_datum.get('attributes.registry-name')}/{list_datum.get('attributes.namespace')}/{list_datum.get('attributes.name')}/{list_datum.get('attributes.provider')}",
                properties=[
                    "attributes.name",
                    "attributes.provider",
                    "attributes.registry-name",
                    "attributes.status",
                    "attributes.vcs-repo.branch",
                    "attributes.vcs-repo.identifier",
                    "id",
                    "relationships.organization.data.id",
                ],
            )[
                0
            ]  # KLUDE: There should be a way to pull single item from the API instead of a list of items

            data.append(module_data)

        logging.info("Stop extracting modules data")

        return data

    def _extract_organization_data(self) -> list[dict]:
        logging.info("Start extracting organizations data")

        properties = ["attributes.email", "attributes.name", "id"]
        data = self._extract_data_from_api(
            include_pattern=self._config.get("include.organizations"), path="/organizations", properties=properties
        )

        logging.info("Stop extracting organizations data")

        return data

    def _extract_policies_data(self, organization: dict) -> list[dict]:
        logging.info("Start extracting policies data")

        properties = [
            "attributes.description",
            "attributes.enforcement-level",
            "attributes.kind",
            "attributes.name",
            "id",
            "relationships.organization.data.id",
        ]
        data = self._extract_data_from_api(
            include_pattern=self._config.get("include.policies"),
            path=f"/organizations/{organization.get('id')}/policies",
            properties=properties,
        )

        logging.info("Stop extracting policies data")

        return data

    def _extract_policy_sets_data(self, organization: dict) -> list[dict]:
        logging.info("Start extracting policy sets data")

        properties = [
            "attributes.description",
            "attributes.enforcement-level",
            "attributes.global",
            "attributes.kind",
            "attributes.name",
            "id",
            "relationships.organization.data.id",
        ]
        data = self._extract_data_from_api(
            include_pattern=self._config.get("include.policy_sets"),
            path=f"/organizations/{organization.get('id')}/policy-sets",
            properties=properties,
        )

        logging.info("Stop extracting policy sets data")

        return data

    def _extract_projects_data(self, organization: dict) -> list[dict]:
        logging.info("Start extracting projects data")

        properties = [
            "attributes.name",
            "id",
            "relationships.organization.data.id",
        ]
        data = self._extract_data_from_api(
            include_pattern=self._config.get("include.projects"),
            path=f"/organizations/{organization.get('id')}/projects",
            properties=properties,
        )

        logging.info("Stop extracting projects data")

        return data

    def _extract_providers_data(self, organization: dict) -> list[dict]:
        logging.info("Start extracting providers data")

        properties = [
            "attributes.name",
            "attributes.namespace",
            "attributes.registry-name",
            "id",
            "relationships.organization.data.id",
        ]
        data = self._extract_data_from_api(
            include_pattern=self._config.get("include.providers"),
            path=f"/organizations/{organization.get('id')}/registry-providers",
            properties=properties,
        )

        logging.info("Stop extracting providers data")

        return data

    def _extract_tasks_data(self, organization: dict) -> list[dict]:
        logging.info("Start extracting tasks data")

        properties = [
            "attributes.category",
            "attributes.description",
            "attributes.enabled",
            "attributes.name",
            "attributes.url",
            "id",
            "relationships.organization.data.id",
        ]
        data = self._extract_data_from_api(
            include_pattern=self._config.get("include.tasks"),
            path=f"/organizations/{organization.get('id')}/tasks",
            properties=properties,
        )

        logging.info("Stop extracting tasks data")

        return data

    def _extract_teams_data(self, organization: dict) -> list[dict]:
        logging.info("Start extracting teams data")

        properties = [
            "attributes.name",
            "attributes.users-count",
            "id",
            "relationships.organization.data.id",
        ]
        data = self._extract_data_from_api(
            include_pattern=self._config.get("include.teams"),
            path=f"/organizations/{organization.get('id')}/teams",
            properties=properties,
        )

        logging.info("Stop extracting teams data")

        return data

    def _extract_variable_sets_data(self, organization: dict) -> list[dict]:
        logging.info("Start extracting variable sets data")

        properties = [
            "attributes.description",
            "attributes.global",
            "attributes.name",
            "attributes.project-count",
            "attributes.var-count",
            "attributes.workspace-count",
            "id",
            "relationships.organization.data.id",
        ]
        data = self._extract_data_from_api(
            include_pattern=self._config.get("include.variable_sets"),
            path=f"/organizations/{organization.get('id')}/varsets",
            properties=properties,
        )

        logging.info("Stop extracting variable sets data")

        return data

    def _extract_workspace_variables_data(self, workspace: dict) -> list[dict]:
        logging.info("Start extracting workspace variables data")

        properties = [
            "attributes.category",
            "attributes.description",
            "attributes.hcl",
            "attributes.key",
            "attributes.sensitive",
            "attributes.value",
            "id",
            "relationships.workspace.data.id",
        ]
        data = self._extract_data_from_api(
            include_pattern=self._config.get("include.workspace_variables"),
            path=f"/workspaces/{workspace.get('id')}/vars",
            properties=properties,
        )

        logging.info("Stop extracting workspace variables data")

        return data

    def _extract_workspaces_data(self, organization: dict) -> list[dict]:
        logging.info("Start extracting workspaces data")

        properties = [
            "attributes.auto-apply",
            "attributes.description",
            "attributes.name",
            "attributes.resource-count",
            "attributes.terraform-version",
            "attributes.vcs-repo.branch",
            "attributes.vcs-repo.identifier",
            "attributes.vcs-repo.service-provider",
            "attributes.working-directory",
            "id",
            "relationships.current-configuration-version.data.id",
            "relationships.current-state-version.data.id",
            "relationships.organization.data.id",
            "relationships.project.data.id",
        ]
        data = self._extract_data_from_api(
            include_pattern=self._config.get("include.workspaces"),
            path=f"/organizations/{organization.get('id')}/workspaces",
            properties=properties,
        )

        logging.info("Stop extracting workspaces data")

        return data

    def _find_entity(self, data: list[dict], id_: str) -> dict | None:
        logging.debug(f"Start searching for entity ({id_})")

        entity = None
        for datum in data:
            if datum.get("id") == id_:
                entity = datum
                break

        logging.debug(f"Stop searching for entity ({id_})")

        return entity

    def _generate_migration_id(self, *args: str) -> str:
        return slugify("_".join(args)).replace("-", "_")

    def _get_plan(self, id_: str) -> dict:
        while True:
            data = self._extract_data_from_api(
                path=f"/plans/{id_}", properties=["attributes.log-read-url", "attributes.status"]
            )[
                0
            ]  # KLUDGE: There should be a way to pull single item from the API instead of a list of items

            if data.get("attributes.status") in ["errored", "finished"]:
                break
            elif data.get("attributes.status") in ["canceled", "unreachable"]:  # noqa: RET508
                logging.warning(f"Plan '{id_}' has status '{data.get('attributes.status')}'. Ignoring.")
                data = {}
                break
            else:
                logging.debug(f"Plan '{id_}' is not finished yet. Waiting 3 seconds before retrying.")
                time.sleep(3)

        return data

    def _map_modules_data(self, src_data: dict) -> dict:
        logging.info("Start mapping modules data")

        data = []
        for module in src_data.get("modules"):
            if module.get("attributes.vcs-repo.identifier"):
                segments = module.get("attributes.vcs-repo.identifier").split("/")
                vcs_namespace = segments[0]
                vcs_repository = segments[1]
            else:
                vcs_namespace = None
                vcs_repository = None

            data.append(
                {
                    "_relationships": {"space": module.get("relationships.organization.data.id")},
                    "_source_id": module.get("id"),
                    "name": module.get("attributes.name"),
                    "status": module.get("attributes.status"),
                    "terraform_provider": module.get("attributes.provider"),
                    "visibility": module.get("attributes.registry-name"),
                    "vcs": {
                        "branch": module.get("attributes.vcs-repo.branch"),
                        "namespace": vcs_namespace,
                        "provider": "github_custom",  # KLUDGE: TFC/TFE does not provide that information
                        "repository": vcs_repository,
                    },
                }
            )

        logging.info("Stop mapping modules data")

        return data

    def _map_spaces_data(self, src_data: dict) -> dict:
        logging.info("Start mapping spaces data")

        data = []
        for organization in src_data.get("organizations"):
            data.append(
                {
                    "_source_id": organization.get("id"),
                    "name": organization.get("attributes.name"),
                }
            )

        logging.info("Stop mapping spaces data")

        return data

    def _map_stack_variables_data(self, src_data: dict) -> dict:
        def find_workspace(data: dict, workspace_id: str) -> dict:
            for workspace in data.get("workspaces"):
                if workspace.get("id") == workspace_id:
                    return workspace

            logging.warning(f"Could not find workspace '{workspace_id}'")

            return None

        logging.info("Start mapping stack variables data")

        prog = re.compile("^[a-zA-Z_]+[a-zA-Z0-9_]*$")
        data = []
        for variable in src_data.get("workspace_variables"):
            workspace = find_workspace(data=src_data, workspace_id=variable.get("relationships.workspace.data.id"))

            is_name_valid = True

            if re.search(prog, variable.get("attributes.key")) is None:
                is_name_valid = False

            data.append(
                {
                    "_relationships": {
                        "space": workspace.get("relationships.organization.data.id"),
                        "stack": variable.get("relationships.workspace.data.id"),
                    },
                    "_source_id": variable.get("id"),
                    "description": variable.get("attributes.description"),
                    "hcl": variable.get("attributes.hcl"),
                    "name": variable.get("attributes.key"),
                    "type": "terraform" if variable.get("attributes.category") == "terraform" else "env_var",
                    "valid_name": is_name_valid,
                    "value": variable.get("attributes.value"),
                    "write_only": variable.get("attributes.sensitive"),
                }
            )

        logging.info("Stop mapping stack variables data")

        return data

    def _map_stacks_data(self, src_data: dict) -> dict:
        def find_workspace_variable_with_invalid_name(data: dict, workspace_id: str, type_: str = "plain") -> dict:
            prog = re.compile("^[a-zA-Z_]+[a-zA-Z0-9_]*$")
            variables = []

            for variable in data.get("workspace_variables"):
                if (variable.get("attributes.sensitive") is True and type_ == "plain") or (
                    variable.get("attributes.sensitive") is False and type_ == "secret"
                ):
                    continue

                if (
                    variable.get("relationships.workspace.data.id") == workspace_id
                    and re.search(prog, variable.get("attributes.key")) is None
                ):
                    variables.append(variable)
                    continue

            return variables

        logging.info("Start mapping stacks data")

        data = []
        for workspace in src_data.get("workspaces"):
            variables_with_invalid_name = find_workspace_variable_with_invalid_name(
                data=src_data, type_="plain", workspace_id=workspace.get("id")
            )
            secret_variables_with_invalid_name = find_workspace_variable_with_invalid_name(
                data=src_data, type_="secret", workspace_id=workspace.get("id")
            )

            provider = workspace.get("attributes.vcs-repo.service-provider")
            if provider is None:
                organization_name = workspace.get("relationships.organization.data.id")
                workspace_name = workspace.get("attributes.name")
                logging.warning(f"Workspace '{organization_name}/{workspace_name}' has no VCS configuration")
            elif provider in ["github", "github_app", "github_enterprise"]:
                provider = "github_custom"
            else:
                raise ValueError(f"Unknown VCS provider name ({provider})")

            if workspace.get("attributes.vcs-repo.identifier"):
                segments = workspace.get("attributes.vcs-repo.identifier").split("/")
                vcs_namespace = segments[0]
                vcs_repository = segments[1]
            else:
                vcs_namespace = None
                vcs_repository = None

            terraform_version = workspace.get("attributes.terraform-version")
            if terraform_version == "latest":
                terraform_version = "1.5.7"

            data.append(
                {
                    "_relationships": {"space": workspace.get("relationships.organization.data.id")},
                    "_source_id": workspace.get("id"),
                    "autodeploy": workspace.get("attributes.auto-apply"),
                    "description": workspace.get("attributes.description"),
                    "has_variables_with_invalid_name": len(variables_with_invalid_name) > 0,
                    "has_secret_variables_with_invalid_name": len(secret_variables_with_invalid_name) > 0,
                    "name": workspace.get("attributes.name"),
                    "slug": self._build_stack_slug(workspace),
                    "terraform": {"version": terraform_version},
                    "vcs": {
                        "branch": workspace.get("attributes.vcs-repo.branch"),
                        "namespace": vcs_namespace,
                        "project_root": workspace.get("attributes.working-directory"),
                        "provider": provider,
                        "repository": vcs_repository,
                    },
                }
            )

        logging.info("Stop mapping stacks data")

        return data

    def _map_data(self, src_data: dict) -> dict:
        logging.info("Start mapping data")

        data = benedict(
            {
                "spaces": self._map_spaces_data(src_data),  # KLUDGE: Must be first due to dependency
                "modules": self._map_modules_data(src_data),
                "stacks": self._map_stacks_data(src_data),
                "stack_variables": self._map_stack_variables_data(src_data),  # Must be after stacks due to dependency
            }
        )

        data = self._expand_relationships(data)

        logging.info("Stop mapping data")

        return data

    def _start_agent_container(self, agent_pool_id: str, container_name: str) -> Container:
        token = self._create_agent_token(agent_pool_id=agent_pool_id)

        container = docker.run(
            detach=True,
            envs={
                "TFC_AGENT_NAME": "SMK-Agent",
                "TFC_AGENT_TOKEN": token,
            },
            image=self._config.get("agent_image", "jmfontaine/tfc-agent:smk-latest"),
            name=container_name,
            pull="always",
            remove=True,
        )

        logging.debug(f"Using TFC/TFE agent Docker container '{container.id}' from image '{container.config.image}'")

        return container

    def _stop_agent_container(self, container: Container):
        if not container.exists() or not container.state.running:
            logging.warning(f"Local TFC/TFE agent '{container}' is already stopped before trying to stop it. Ignoring.")

        logging.debug(f"Stopping TFC/TFE agent Docker container '{container.id}' from image '{container.config.image}'")
        container.stop()
