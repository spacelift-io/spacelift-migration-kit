# ruff: noqa: TRY002, TRY003
import json
from collections import defaultdict
from http import HTTPStatus
from pathlib import Path

import requests
from flatten_dict import flatten
from slugify import slugify


class Exporter:
    def __init__(self, console, api_token, api_endpoint="https://app.terraform.io"):
        self._api_endpoint = api_endpoint
        self._api_token = api_token
        self._console = console

    def _add_agent_pool_checks(self, items):
        for key, item in enumerate(items):
            issues = []

            if "agent-count" in item["attributes"] and item["attributes"]["agent-count"] == 0:
                issues.append("No agents")

            items[key]["issues"] = issues

        return items

    def _add_policy_checks(self, items):
        for key, item in enumerate(items):
            issues = []

            if "kind" in item["attributes"]:
                if item["attributes"]["kind"] == "sentinel":
                    issues.append("Sentinel policy")
            else:
                # Older Terraform Enterprise versions only supported Sentinel policies
                issues.append("Sentinel policy")

            items[key]["issues"] = issues

        return items

    def _add_workspace_checks(self, items):
        for key, item in enumerate(items):
            issues = []

            if "resource-count" in item["attributes"] and item["attributes"]["resource-count"] == 0:
                issues.append("No resources")

            items[key]["issues"] = issues

        return items

    def _call_api(self, api_path):
        headers = {
            "Authorization": f"Bearer {self._api_token}",
            "Content-Type": "application/vnd.api+json",
        }
        data = []
        url = f"{self._api_endpoint}/api/v2{api_path}"

        while True:
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                # Return None for non-existent API endpoints as we are most likely interacting with an older TFE version
                if e.response.status_code == HTTPStatus.NOT_FOUND:
                    self._console.print(f"[warning]Warning: Non-existent API endpoint ({url}). Ignoring.[/warning]")
                    return None

                raise Exception(f"HTTP Error: {e}") from e
            except requests.exceptions.ReadTimeout as e:
                raise Exception(f"Timeout for {url}") from e
            except requests.exceptions.ConnectionError as e:
                raise Exception(f"Connection error for {url}") from e
            except requests.exceptions.RequestException as e:
                raise Exception(f"Error for {url}") from e

            payload = response.json()
            for item in payload["data"]:
                data.append(item)  # noqa: PERF402 - https://github.com/astral-sh/ruff/issues/5580

            if "links" in payload and payload["links"]["next"]:
                url = payload["links"]["next"]
            else:
                break

        return data

    def _get_items(self, api_path, attributes, sensitive_attributes=None, include_sensitive_attributes=False):
        if sensitive_attributes is None:
            sensitive_attributes = []

        if include_sensitive_attributes is True:
            attributes = attributes + sensitive_attributes

        data = self._call_api(api_path)
        # Some non-critical problem occurred and no data could be retrieved
        if data is None:
            return []

        items = []
        for datum in data:
            flat_datum = flatten(datum, reducer="dot")
            item = {}
            if "id" in flat_datum:
                item["id"] = flat_datum["id"]
            for attribute in attributes:
                if f"attributes.{attribute}" in flat_datum:
                    # Older TFE versions might not have all the attributes. We still want the attribute to exist
                    # to avoid downstream errors or unnecessary checking so we use None as the default value.
                    item[attribute] = flat_datum.get(f"attributes.{attribute}", None)

            items.append({"attributes": item})

        return items

    def _list_agent_pools(self, organization_id):
        attributes = [
            "agent-count",
            "name",
            "organization-scoped",
        ]

        return self._get_items(f"/organizations/{organization_id}/agent-pools", attributes)

    def _list_organizations(self):
        attributes = []

        return self._get_items("/organizations", attributes)

    def _list_policies(self, organization_id):
        attributes = [
            "description",
            "enforcement-level",
            "kind",
            "name",
        ]

        return self._get_items(f"/organizations/{organization_id}/policies", attributes)

    def _list_policy_sets(self, organization_id):
        attributes = [
            "description",
            "enforcement-level",
            "global",
            "kind",
            "name",
        ]

        return self._get_items(f"/organizations/{organization_id}/policy-sets", attributes)

    def _list_projects(self, organization_id):
        attributes = ["name"]

        return self._get_items(f"/organizations/{organization_id}/projects", attributes)

    def _list_registry_modules(self, organization_id):
        attributes = [
            "name",
            "namespace",
            "provider",
            "status",
        ]

        return self._get_items(f"/organizations/{organization_id}/registry-modules", attributes)

    def _list_registry_providers(self, organization_id):
        attributes = [
            "name",
            "namespace",
            "registry-name",
        ]

        return self._get_items(f"/organizations/{organization_id}/registry-modules", attributes)

    def _list_tasks(self, organization_id):
        attributes = [
            "category",
            "description",
            "enabled",
            "name",
            "url",
        ]

        return self._get_items(f"/organizations/{organization_id}/tasks", attributes)

    def _list_teams(self, organization_id):
        attributes = [
            "name",
            "users-count",
        ]

        return self._get_items(f"/organizations/{organization_id}/teams", attributes)

    def _list_variable_sets(self, organization_id):
        attributes = [
            "description",
            "global",
            "name",
            "project-count",
            "var-count",
            "workspace-count",
        ]

        return self._get_items(f"/organizations/{organization_id}/varsets", attributes)

    def _list_variables(self, workspace_id, include_sensitive_attributes=False):
        attributes = [
            "category",
            "description",
            "hcl",
            "key",
            "name",
            "sensitive",
        ]

        sensitive_attributes = [
            "value",
        ]

        return self._get_items(
            f"/workspaces/{workspace_id}/vars",
            attributes=attributes,
            sensitive_attributes=sensitive_attributes,
            include_sensitive_attributes=include_sensitive_attributes,
        )

    def _list_workspaces(self, organization_id):
        attributes = [
            "auto-apply",
            "description",
            "name",
            "resource-count",
            "terraform-version",
            "vcs-repo.branch",
            "vcs-repo.repository-http-url",
            "working-directory",
        ]

        return self._get_items(f"/organizations/{organization_id}/workspaces", attributes)

    def _check_items(self, item_type: str, items: dict) -> dict:
        if item_type == "agent_pools":
            items = self._add_agent_pool_checks(items)
        elif item_type == "policies":
            items = self._add_policy_checks(items)
        elif item_type == "workspaces":
            items = self._add_workspace_checks(items)

        return items

    def audit(self):
        data = self._extract_data(include_sensitive_attributes=False)

        for entity_type, entity_list in sorted(data.items()):
            entity_list = self._check_items(entity_type, entity_list)  # noqa: PLW2901

            title = entity_type.replace("_", " ").title()
            count = len(entity_list)
            entities_with_issues = [e for e in entity_list if "issues" in e and len(e["issues"]) > 0]
            with_issues_count = len(entities_with_issues)
            with_issues_message = f" (including {with_issues_count} with issues)" if with_issues_count > 0 else ""

            self._console.print(f"{title}: {count}{with_issues_message}")

            for entity in entities_with_issues:
                entity_id = entity["attributes"]["id"]
                entity_name = f" ({entity['attributes' ]['name']})" if "name" in entity["attributes"] else ""
                issues = ", ".join(entity["issues"])
                self._console.print(f"  - {entity_id}{entity_name}: {issues}", style="warning")

    def _extract_data(self, include_sensitive_attributes=False) -> dict:
        """Retrieve data from the source vendor

        Args:
            include_sensitive_attributes (bool): Include sensitive data when exporting

        Returns:
            dict: The extracted data
        """
        # Make non-existent keys an empty list to simplify the implementation
        data = defaultdict(list)

        organizations = self._list_organizations()
        data["organizations"] = organizations

        for organization in organizations:
            organization_id = organization["attributes"]["id"]

            data["agent_pools"].extend(self._list_agent_pools(organization_id))
            data["policies"].extend(self._list_policies(organization_id))
            data["policy_sets"].extend(self._list_policy_sets(organization_id))
            data["projects"].extend(self._list_projects(organization_id))
            data["registry_modules"].extend(self._list_registry_modules(organization_id))
            data["registry_providers"].extend(self._list_registry_providers(organization_id))
            data["tasks"].extend(self._list_tasks(organization_id))
            data["teams"].extend(self._list_teams(organization_id))
            data["variable_sets"].extend(self._list_variable_sets(organization_id))

            workspaces = self._list_workspaces(organization_id)
            data["workspaces"].extend(workspaces)

            for workspace in workspaces:
                workspace_id = workspace["attributes"]["id"]
                data["variables"].extend(
                    self._list_variables(workspace_id, include_sensitive_attributes=include_sensitive_attributes)
                )

        return data

    def _generate_id_from_name(self, name: str) -> str:
        return slugify(name)

    def _transform_data(self, raw_data: dict) -> dict:
        """Map the data extracted from the source vendor to Spacelift entities

        Args:
            raw_data (dict): Data extracted from the source vendor

        Returns:
            dict: Spacelift entities data
        """
        data = {"stacks": []}

        for workspace in raw_data["workspaces"]:
            attributes = workspace["attributes"]
            data["stacks"].append(
                {
                    "autodeploy": attributes["auto-apply"],
                    "branch": attributes["vcs-repo.branch"],
                    "description": attributes["description"],
                    "id": self._generate_id_from_name(attributes["name"]),
                    "name": attributes["name"],
                    "project_root": attributes["working-directory"],
                    "repository": attributes["vcs-repo.repository-http-url"],
                    "terraform_version": attributes["terraform-version"],
                }
            )

        return data

    def _save_to_file(self, data: dict):
        """Save the Spacelift entities data to a JSON file

        Args:
            data (dict): Spacelift entities data
        """
        folder = Path(f"{__file__}/../../../tmp").resolve()
        if not Path.exists(folder):
            Path.mkdir(folder, parents=True)

        with Path(f"{folder}/data.json").open("w") as fp:
            json.dump(data, fp, indent=2, sort_keys=True)

    def export(self):
        """Export data from the source vendor to Spacelift entities data and store that in a JSON file"""
        data = self._extract_data(include_sensitive_attributes=True)
        data = self._transform_data(data)
        self._save_to_file(data)
