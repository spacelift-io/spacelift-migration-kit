# ruff: noqa: PERF401
import logging
import re
from http import HTTPStatus

import requests
from benedict import benedict
from rich.console import Console
from slugify import slugify

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

    def _call_api(self, url: str, method: str = "GET") -> dict:
        logging.debug("Start calling API")

        headers = {
            "Authorization": f"Bearer {self._config.get('api_token')}",
            "Content-Type": "application/vnd.api+json",
        }

        try:
            response = requests.request(headers=headers, method=method, url=url)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            # Return None for non-existent API endpoints as we are most likely interacting with an older TFE version
            if e.response.status_code == HTTPStatus.NOT_FOUND:
                logging.warning(f"Non-existent API endpoint ({url}). Ignoring.")
                return None

            raise Exception(f"HTTP Error: {e}") from e  # noqa: TRY002
        except requests.exceptions.ReadTimeout as e:
            raise Exception(f"Timeout for {url}") from e  # noqa: TRY002
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Connection error for {url}") from e  # noqa: TRY002
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error for {url}") from e  # noqa: TRY002

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
            data["workspaces"].extend(self._extract_workspaces_data(organization))

        for workspace in data.workspaces:
            data["workspace_variables"].extend(self._extract_workspace_variables_data(workspace))

        logging.debug("Stop extracting data")

        return data

    def _extract_data_from_api(
        self, path: str, include_pattern: str | None = None, method: str = "GET", properties: list | None = None
    ) -> list[dict]:
        logging.debug("Start extracting data from API")

        if include_pattern is None:
            include_pattern = ".*"

        endpoint = self._config.get("api_endpoint", "https://app.terraform.io")
        url = f"{endpoint}/api/v2{path}"

        raw_data = []
        while True:
            response_payload = self._call_api(url, method=method)
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
            elif provider == "github":
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
