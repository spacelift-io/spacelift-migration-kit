# ruff: noqa: PERF401
import json
import logging
import re
import time
from http import HTTPStatus
from pathlib import Path

import pydash
import requests
from benedict import benedict
from python_on_whales import docker
from python_on_whales.exceptions import NoSuchContainer
from requests_toolbelt.utils import dump as request_dump
from rich.console import Console
from slugify import slugify

from spacemk import is_command_available

from .base import BaseExporter


class TerraformExporter(BaseExporter):
    def __init__(self, config: dict, console: Console):
        super().__init__(config, console)

        self._property_mapping = {
            "organizations": {
                "attributes.email": "properties.email",
                "attributes.name": "properties.name",
                "id": "properties.id",
            }
        }

    def _call_api(
        self,
        url: str,
        drop_response_properties: list | None = None,
        method: str = "GET",
        request_data: dict | None = None,
    ) -> dict:
        logging.debug("Start calling API")

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

            raise Exception(f"HTTP Error: {e}") from e  # noqa: TRY002
        except requests.exceptions.ReadTimeout as e:
            raise Exception(f"Timeout for {url}") from e  # noqa: TRY002
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Connection error for {url}") from e  # noqa: TRY002
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error for {url}") from e  # noqa: TRY002

        if drop_response_properties:
            # Drop properties, mostly when they contain the keypath separator benedict uses (ie ".")
            data = benedict(pydash.omit(response.json(), drop_response_properties))
        elif len(response.content) == 0:
            # The response has no content (e.g. 204 HTTP status code)
            data = benedict()
        else:
            data = benedict(response.json())

        logging.debug("Stop calling API")

        return data

    def _check_data(self, data: list[dict]) -> list[dict]:
        logging.debug("Start checking data")

        data["agent_pools"] = self._check_agent_pools_data(data.get("agent_pools"))
        data["policies"] = self._check_policies_data(data.get("policies"))
        data["workspaces"] = self._check_workspaces_data(data.get("workspaces"))

        logging.debug("Stop checking data")

        return data

    def _check_agent_pools_data(self, data: list[dict]) -> list[dict]:
        logging.debug("Start checking agent pools data")

        for key, item in enumerate(data):
            warnings = []

            if item.get("attributes.agent-count") == 0:
                warnings.append("No agents")

            data[key]["warnings"] = ", ".join(warnings)

        logging.debug("Stop checking agent pools data")

        return data

    def _check_policies_data(self, data: list[dict]) -> list[dict]:
        logging.debug("Start checking policies data")

        for key, item in enumerate(data):
            warnings = []

            # Older Terraform Enterprise versions only supported Sentinel policies
            if not item.get("attributes.kind") or item.get("attributes.kind") == "sentinel":
                warnings.append("Sentinel policy")

            data[key]["warnings"] = ", ".join(warnings)

        logging.debug("Stop checking policies data")

        return data

    def _check_workspaces_data(self, data: list[dict]) -> list[dict]:
        logging.debug("Start checking workspaces data")

        for key, item in enumerate(data):
            warnings = []

            if item.get("attributes.resource-count") == 0:
                warnings.append("No resources")

            if item.get("attributes.vcs-repo.service-provider") is None:
                warnings.append("No VCS configuration")

            data[key]["warnings"] = ", ".join(warnings)

        logging.debug("Stop checking workspaces data")

        return data

    def _download_text_file(self, url: str) -> str:
        logging.debug("Start downloading text file")

        headers = {
            "Authorization": f"Bearer {self._config.get('api_token')}",
        }
        response = requests.get(allow_redirects=True, headers=headers, url=url)

        logging.debug("Stop downloading text file")

        return response.text

    def _download_state_files(self, data: dict) -> None:
        logging.debug("Start downloading state files")

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

                organization_id = workspace.get("relationships.organization.data.id")
                workspace_id = workspace.get("id")

                folder = Path(f"{__file__}/../../../tmp/state-files/{organization_id}").resolve()
                if not Path.exists(folder):
                    Path.mkdir(folder, parents=True)

                file_path = f"{folder}/{workspace_id}.tfstate"
                with Path(file_path).open("w", encoding="utf-8") as fp:
                    logging.debug(f"Saving state file for '{organization_id}/{workspace_id}' to '{file_path}'")
                    fp.write(state_file_content)

        logging.debug("Stop downloading state files")

    # KLUDGE: We should break this function down in smaller functions
    def _enrich_workspace_variable_data(self, data: dict) -> dict:  # noqa: PLR0915
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

        if not is_command_available("docker ps", execute=True):
            logging.warning("Docker is not installed. Skipping enriching workspace variables data.")
            return data

        logging.debug("Start enriching workspace variables data")

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
            tfc_agent_token_id = agent_token_data[0].get("id")
            tfc_agent_token = agent_token_data[0].get("attributes.token")
            logging.info(f"Created '{tfc_agent_token_id}' agent token")

            try:
                with docker.run(
                    "jmfontaine/tfc-agent:smk-1",
                    detach=True,
                    envs={
                        "TFC_AGENT_NAME": "SMK-Agent",
                        "TFC_AGENT_TOKEN": tfc_agent_token,
                    },
                    name=f"smk-tfc-agent-{organization_id}",
                    remove=True,
                ) as tfc_agent_container_id:
                    logging.debug(f"Running TFC Agent Docker container '{tfc_agent_container_id}'")

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

                        logging.info(f"Restoring the '{organization_id}/{workspace_id}' workspace execution mode")
                        self._extract_data_from_api(
                            method="PATCH",
                            path=f"/workspaces/{workspace_id}",
                            request_data={
                                "data": {
                                    "attributes": {
                                        "execution-mode": workspace_data_backup.get("attributes.execution-mode"),
                                        "setting-overwrites": workspace_data_backup.get(
                                            "attributes.setting-overwrites"
                                        ),
                                    },
                                    "relationships": {
                                        "agent-pool": workspace_data_backup.get("relationships.agent-pool"),
                                    },
                                    "type": "workspaces",
                                }
                            },
                        )

                        logging.info("Retrieve the output for the plan")
                        plan_id = run_data.get("relationships.plan.data.id")
                        plan_data = self._extract_data_from_api(
                            path=f"/plans/{plan_id}", properties=["attributes.log-read-url"]
                        )[
                            0
                        ]  # KLUDGE: There should be a way to pull single item from the API instead of a list of items
                        # KLUDGE: Looks like the logs are not immediately available.
                        # If the logs are not available the response will have a 200 HTTP status but an empty body.
                        # Ideally, we should check for this, wait, and try again until it succeeds.
                        time.sleep(30)
                        logs_data = self._download_text_file(url=plan_data.get("attributes.log-read-url"))

                        logging.info("Extract the env var values from the plan output")
                        for line in logs_data.split("\n"):
                            for workspace_variable_id, workspace_variable_name in workspace_variables.items():
                                prefix = f"{workspace_variable_name}="
                                if line.startswith(prefix):
                                    variable = find_variable(data, workspace_variable_id)
                                    variable["attributes.value"] = line.removeprefix(prefix)

            except NoSuchContainer as e:
                logging.warning(
                    f"Could not find TFC Agent Docker container '{tfc_agent_container_id}' to stop it. Ignoring."
                )
                logging.debug(e)

                logging.info(f"Stop local TFC/TFE agent for organization '{organization_id}'")

            logging.info(f"Deleting '{agent_pool_id}' agent pool")
            self._extract_data_from_api(
                method="DELETE",
                path=f"/agent-pools/{agent_pool_id}",
            )

        logging.info("Stop enriching workspace variables data")

        return data

    def _enrich_data(self, data: dict) -> dict:
        logging.debug("Start enriching data")

        self._download_state_files(data)
        data = self._enrich_workspace_variable_data(data)

        logging.debug("Stop enriching data")

        return data

    def _expand_relationships(self, data: dict) -> dict:
        def find_entity(data: dict, type_: str, id_: str) -> dict:
            # Pluralize the type
            type_ = f"{type_}s"
            for src_datum in data.get(type_):
                # Clone to avoid modifying the original dict when removing the relationships
                # on the expanded relationship
                datum = src_datum.clone()

                if datum.get("_source_id") == id_:
                    del datum["_relationships"]

                    return datum

            return None

        logging.debug("Start expanding relationships")

        for entity_data in data.values():
            for datum in entity_data:
                relationships = {}
                if datum.get("_relationships"):
                    for type_, id_ in datum.get("_relationships").items():
                        relationships[type_] = find_entity(data=data, id_=id_, type_=type_)

                datum.update(
                    {"_migration_id": self._generate_migration_id(datum.get("name")), "_relationships": relationships}
                )

        logging.debug("Stop expanding relationships")

        return data

    def _extract_data(self) -> list[dict]:
        logging.debug("Start extracting data")
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

        logging.debug("Stop extracting data")

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
        logging.debug("Start extracting data from API")

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

        logging.debug("Stop extracting data from API")

        return data

    def _extract_agent_pools_data(self, organization: dict) -> list[dict]:
        logging.debug("Start extracting agent pools data")

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

        logging.debug("Stop extracting agent pools data")

        return data

    def _extract_modules_data(self, organization: dict) -> list[dict]:
        logging.debug("Start extracting modules data")

        properties = [
            "attributes.name",
            "attributes.namespace",
            "attributes.provider",
            "attributes.status",
            "id",
            "relationships.organization.data.id",
        ]
        data = self._extract_data_from_api(
            include_pattern=self._config.get("include.modules"),
            path=f"/organizations/{organization.get('id')}/registry-modules",
            properties=properties,
        )

        logging.debug("Stop extracting modules data")

        return data

    def _extract_organization_data(self) -> list[dict]:
        logging.debug("Start extracting organizations data")

        properties = ["attributes.email", "attributes.name", "id"]
        data = self._extract_data_from_api(
            include_pattern=self._config.get("include.organizations"), path="/organizations", properties=properties
        )

        logging.debug("Stop extracting organizations data")

        return data

    def _extract_policies_data(self, organization: dict) -> list[dict]:
        logging.debug("Start extracting policies data")

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

        logging.debug("Stop extracting policies data")

        return data

    def _extract_policy_sets_data(self, organization: dict) -> list[dict]:
        logging.debug("Start extracting policy sets data")

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

        logging.debug("Stop extracting policy sets data")

        return data

    def _extract_projects_data(self, organization: dict) -> list[dict]:
        logging.debug("Start extracting projects data")

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

        logging.debug("Stop extracting projects data")

        return data

    def _extract_providers_data(self, organization: dict) -> list[dict]:
        logging.debug("Start extracting providers data")

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

        logging.debug("Stop extracting providers data")

        return data

    def _extract_tasks_data(self, organization: dict) -> list[dict]:
        logging.debug("Start extracting tasks data")

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

        logging.debug("Stop extracting tasks data")

        return data

    def _extract_teams_data(self, organization: dict) -> list[dict]:
        logging.debug("Start extracting teams data")

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

        logging.debug("Stop extracting teams data")

        return data

    def _extract_variable_sets_data(self, organization: dict) -> list[dict]:
        logging.debug("Start extracting variable sets data")

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

        logging.debug("Stop extracting variable sets data")

        return data

    def _extract_workspace_variables_data(self, workspace: dict) -> list[dict]:
        logging.debug("Start extracting workspace variables data")

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

        logging.debug("Stop extracting workspace variables data")

        return data

    def _extract_workspaces_data(self, organization: dict) -> list[dict]:
        logging.debug("Start extracting workspaces data")

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

        logging.debug("Stop extracting workspaces data")

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

    def _map_spaces_data(self, src_data: dict) -> dict:
        logging.debug("Start mapping spaces data")

        data = []
        for organization in src_data.get("organizations"):
            data.append(
                {
                    "_source_id": organization.get("id"),
                    "name": organization.get("attributes.name"),
                }
            )

        logging.debug("Stop mapping spaces data")

        return data

    def _map_stack_variables_data(self, src_data: dict) -> dict:
        logging.debug("Start mapping stack variables data")

        data = []
        for variable in src_data.get("workspace_variables"):
            data.append(
                {
                    "_relationships": {"stack": variable.get("relationships.workspace.data.id")},
                    "_source_id": variable.get("id"),
                    "description": variable.get("attributes.description"),
                    "name": variable.get("attributes.key"),
                    "value": variable.get("attributes.value"),
                    "write_only": variable.get("attributes.sensitive"),
                }
            )

        logging.debug("Stop mapping stack variables data")

        return data

    def _map_stacks_data(self, src_data: dict) -> dict:
        logging.debug("Start mapping stacks data")

        data = []
        for workspace in src_data.get("workspaces"):
            provider = workspace.get("attributes.vcs-repo.service-provider")
            if provider is None:
                organization_name = workspace.get("relationships.organization.data.id")
                workspace_name = workspace.get("attributes.name")
                logging.warning(f"Workspace '{organization_name}/{workspace_name}' has no VCS configuration")
            elif provider in ["github", "github_enterprise"]:
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

            data.append(
                {
                    "_relationships": {"space": workspace.get("relationships.organization.data.id")},
                    "_source_id": workspace.get("id"),
                    "autodeploy": workspace.get("attributes.auto-apply"),
                    "description": workspace.get("attributes.description"),
                    "name": workspace.get("attributes.name"),
                    "terraform": {"version": workspace.get("attributes.terraform-version")},
                    "vcs": {
                        "branch": workspace.get("attributes.vcs-repo.branch"),
                        "namespace": vcs_namespace,
                        "project_root": workspace.get("attributes.vcs-repo.working-directory"),
                        "provider": provider,
                        "repository": vcs_repository,
                    },
                }
            )

        logging.debug("Stop mapping stacks data")

        return data

    def _map_data(self, src_data: dict) -> dict:
        logging.debug("Start mapping data")

        data = benedict(
            {
                "spaces": self._map_spaces_data(src_data),
                "stacks": self._map_stacks_data(src_data),
                "stack_variables": self._map_stack_variables_data(src_data),  # Must be after stacks due to dependency
            }
        )

        data = self._expand_relationships(data)

        logging.debug("Stop mapping data")

        return data
