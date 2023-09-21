import requests

from flatten_dict import flatten
from pprint import pprint


class Exporter:
    def __init__(
        self, api_token, api_endpoint="https://app.terraform.io", edition="tfc"
    ):
        self.api_endpoint = api_endpoint
        self.api_token = api_token

        if api_endpoint == "https://app.terraform.io":
            self.edition = "tfc"
        else:
            self.edition = "tfe"

    def _call_api(self, url):
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/vnd.api+json",
        }

        request = requests.get(url, headers=headers)

        # TODO: Handle errors

        return request.json()

    def _get_data(self, api_path):
        data = []
        url = f"{self.api_endpoint}/api/v2{api_path}"

        while True:
            response = self._call_api(url)
            for item in response["data"]:
                data.append(item)

            if "links" not in response or response["links"]["next"] is None:
                break
            else:
                url = response["links"]["next"]

        return data

    def _get_entities(self, api_path, attributes=[]):
        raw_data = self._get_data(api_path)

        entities = []

        for datum in raw_data:
            datum = flatten(datum, reducer="dot")
            entity = {}
            for attribute in attributes:
                if f"attributes.{attribute}" in datum:
                    entity[attribute] = datum[f"attributes.{attribute}"]
            if "id" in datum:
                entity["id"] = datum["id"]
            entities.append(entity)

        return entities

    def _list_agent_pools(self, organization_id):
        attributes = [
            "agent-count",
            "name",
            "organization-scoped",
        ]
        return self._get_entities(
            f"/organizations/{organization_id}/agent-pools", attributes
        )

    def _list_organizations(self):
        return self._get_entities("/organizations")

    def _list_policies(self, organization_id):
        attributes = [
            "description",
            "enforcement-level",
            "kind",
            "name",
        ]
        return self._get_entities(
            f"/organizations/{organization_id}/policies", attributes
        )

    def _list_policy_sets(self, organization_id):
        attributes = [
            "description",
            "enforcement-level",
            "global",
            "kind",
            "name",
        ]
        return self._get_entities(
            f"/organizations/{organization_id}/policy-sets", attributes
        )

    def _list_projects(self, organization_id):
        attributes = [
            "name"
        ]
        return self._get_entities(
            f"/organizations/{organization_id}/projects", attributes
        )

    def _list_registry_modules(self, organization_id):
        attributes = [
            "name",
            "namespace",
            "provider",
            "status",
        ]
        return self._get_entities(
            f"/organizations/{organization_id}/registry-modules", attributes
        )

    def _list_registry_providers(self, organization_id):
        attributes = [
            "name",
            "namespace",
            "registry-name",
        ]
        return self._get_entities(
            f"/organizations/{organization_id}/registry-modules", attributes
        )

    def _list_tasks(self, organization_id):
        attributes = [
            "category", "description", "enabled", "name", "url",
        ]
        return self._get_entities(
            f"/organizations/{organization_id}/tasks", attributes
        )

    def _list_workspaces(self, organization_id):
        attributes = [
            "auto-apply", "description", "name", "resource-count", "terraform-version", "vcs-repo.branch", "vcs-repo.repository-http-url", "working-directory",
        ]
        return self._get_entities(
            f"/organizations/{organization_id}/workspaces", attributes
        )

    def audit(self):
        organizations = self._list_organizations()

        stats = {
            "organizations": len(organizations),
        }
        for organization in organizations:
            # agent_pools = self._list_agent_pools(organization["id"])
            # stats["agent_pools"] = len(agent_pools)

            # policies = self._list_policies(organization["id"])
            # stats["policies"] = len(policies)

            # policy_sets = self._list_policy_sets(organization["id"])
            # stats["policy_sets"] = len(policy_sets)

            # projects = self._list_projects(organization["id"])
            # stats["projects"] = len(projects)

            # registry_modules = self._list_registry_modules(organization["id"])
            # stats["registry_modules"] = len(registry_modules)

            # registry_providers = self._list_registry_providers(organization["id"])
            # stats["registry_providers"] = len(registry_providers)

            # tasks = self._list_tasks(organization["id"])
            # stats["tasks"] = len(tasks)

            workspaces = self._list_workspaces(organization["id"])
            pprint(workspaces)
            stats["workspaces"] = len(workspaces)

        tf_edition_name = "Cloud" if self.edition == "tfc" else "Enterprise"
        print(f"Detected Terraform {tf_edition_name}")

        pprint(stats)
