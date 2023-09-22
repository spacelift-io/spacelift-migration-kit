import requests

from collections import defaultdict
from flatten_dict import flatten

class Exporter:
    def __init__(
        self, console, api_token, api_endpoint="https://app.terraform.io"):
        self._api_endpoint = api_endpoint
        self._api_token = api_token

        self._console = console

        if api_endpoint == "https://app.terraform.io":
            self.edition = "tfc"
        else:
            self.edition = "tfe"

    def _add_agent_pool_checks(self, items):
        for key, item in enumerate(items):
            issues = []

            if item["properties"]["agent-count"] == 0:
              issues.append("No agents")

            items[key]["issues"] = issues

        return items

    def _add_policy_checks(self, items):
        for key, item in enumerate(items):
            issues = []

            if item["properties"]["kind"] == "sentinel":
              issues.append("Sentinel policy")

            items[key]["issues"] = issues

        return items

    def _add_workspace_checks(self, items):
        for key, item in enumerate(items):
            issues = []

            if item["properties"]["resource-count"] == 0:
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
            # TODO: Handle errors
            response = requests.get(url, headers=headers).json()

            for item in response["data"]:
                data.append(item)

            if "links" not in response or response["links"]["next"] is None:
                break
            else:
                url = response["links"]["next"]

        return data

    def _get_items(self, api_path, attributes=[]):
        data = self._call_api(api_path)
        items = []

        for datum in data:
            datum = flatten(datum, reducer="dot")
            item = {}
            for attribute in attributes:
                if f"attributes.{attribute}" in datum:
                    item[attribute] = datum[f"attributes.{attribute}"]
            if "id" in datum:
                item["id"] = datum["id"]
            items.append({"properties": item})

        return items

    def _list_agent_pools(self, organization_id, check=False):
        attributes = [
            "agent-count",
            "name",
            "organization-scoped",
        ]

        items =  self._get_items(
            f"/organizations/{organization_id}/agent-pools", attributes
        )

        if check:
            items = self._add_agent_pool_checks(items)

        return items

    def _list_entities(self, check=True):
        entities = defaultdict(list)

        organizations = self._list_organizations()
        entities["organizations"] = organizations

        for organization in organizations:
            organization_id = organization["properties"]["id"]

            entities["agent_pools"].extend(self._list_agent_pools(organization_id, check=check))
            entities["policies"].extend(self._list_policies(organization_id, check=check))
            entities["policy_sets"].extend(self._list_policy_sets(organization_id))
            entities["projects"].extend(self._list_projects(organization_id))
            entities["registry_modules"].extend(self._list_registry_modules(organization_id))
            entities["registry_providers"].extend(self._list_registry_providers(organization_id))
            entities["tasks"].extend(self._list_tasks(organization_id))
            entities["teams"].extend(self._list_teams(organization_id))
            entities["variable_sets"].extend(self._list_variable_sets(organization_id))

            workspaces = self._list_workspaces(organization_id, check=check)
            entities["workspaces"].extend(workspaces)

            for workspace in workspaces:
                workspace_id = workspace["properties"]["id"]
                entities["variables"].extend(self._list_variables(workspace_id))

        return entities

    def _list_organizations(self):
        return self._get_items("/organizations")

    def _list_policies(self, organization_id, check=False):
        attributes = [
            "description",
            "enforcement-level",
            "kind",
            "name",
        ]

        items = self._get_items(
            f"/organizations/{organization_id}/policies", attributes
        )

        if check:
            items = self._add_policy_checks(items)

        return items

    def _list_policy_sets(self, organization_id):
        attributes = [
            "description",
            "enforcement-level",
            "global",
            "kind",
            "name",
        ]
        return self._get_items(
            f"/organizations/{organization_id}/policy-sets", attributes
        )

    def _list_projects(self, organization_id):
        attributes = [
            "name"
        ]
        return self._get_items(
            f"/organizations/{organization_id}/projects", attributes
        )

    def _list_registry_modules(self, organization_id):
        attributes = [
            "name",
            "namespace",
            "provider",
            "status",
        ]
        return self._get_items(
            f"/organizations/{organization_id}/registry-modules", attributes
        )

    def _list_registry_providers(self, organization_id):
        attributes = [
            "name",
            "namespace",
            "registry-name",
        ]
        return self._get_items(
            f"/organizations/{organization_id}/registry-modules", attributes
        )

    def _list_tasks(self, organization_id):
        attributes = [
            "category", "description", "enabled", "name", "url",
        ]
        return self._get_items(
            f"/organizations/{organization_id}/tasks", attributes
        )

    def _list_teams(self, organization_id):
        attributes = [
            "name", "users-count",
        ]
        return self._get_items(
            f"/organizations/{organization_id}/teams", attributes
        )

    def _list_variable_sets(self, organization_id):
        attributes = [
            "description", "global", "name", "project-count", "var-count", "workspace-count",
        ]
        return self._get_items(
            f"/organizations/{organization_id}/varsets", attributes
        )

    def _list_variables(self, workspace_id):
        attributes = [
            "category", "description", "hcl", "key", "name", "sensitive",
        ]
        return self._get_items(
            f"/workspaces/{workspace_id}/vars", attributes
        )

    def _list_workspaces(self, organization_id, check=False):
        attributes = [
            "auto-apply", "description", "name", "resource-count", "terraform-version", "vcs-repo.branch", "vcs-repo.repository-http-url", "working-directory",
        ]

        items = self._get_items(
            f"/organizations/{organization_id}/workspaces", attributes
        )

        if check:
            items = self._add_workspace_checks(items)

        return items

    def audit(self):
        entities = self._list_entities(check=True)

        for entity_type, entity_list in sorted(entities.items()):
            title = entity_type.replace('_', ' ').title()
            count = len(entity_list)
            entities_with_issues = [e for e in entity_list if "issues" in e and len(e["issues"]) > 0]
            with_issues_count = len(entities_with_issues)
            with_issues_message = f" (including {with_issues_count} with issues)" if with_issues_count > 0 else ""

            self._console.print(f"{title}: {count}{with_issues_message}")

            for entity in entities_with_issues:
                entity_id = entity["properties"]["id"]
                entity_name = f" ({entity['properties' ]['name']})" if "name" in entity["properties"] else ""
                issues = ", ".join(entity["issues"])
                self._console.print(f"  - {entity_id}{entity_name}: {issues}", style="warning")
