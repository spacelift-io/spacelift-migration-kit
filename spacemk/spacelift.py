import logging
import os
from base64 import b64encode

import requests
from benedict import benedict
from requests_toolbelt.utils import dump as request_dump

from spacemk import load_normalized_data


class Spacelift:
    def __init__(self, config: dict) -> None:
        """Constructor

        Args:
            config (dict): Configuration
        """
        self._config = config
        self._api_jwt_token = None

    def _call_api(self, operation: str, variables: dict | None = None) -> dict:
        try:
            response = requests.post(
                headers={"Authorization": f"Bearer {self._get_api_jwt_token()}"},
                json={"query": operation, "variables": variables},
                url=self._config.get("api.api_key_endpoint"),
            )
            logging.debug(request_dump.dump_all(response).decode("utf-8"))
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"HTTP Error: {e}") from e

        data = benedict(response.json())

        if "errors" in data:
            logging.warning(data.get("errors[0].message"))

        return data

    def _get_api_jwt_token(self) -> str:
        if not self._api_jwt_token:
            query = """
              mutation GetSpaceliftToken($apiKeyId: ID!, $apiKeySecret: String!) {
                apiKeyUser(id: $apiKeyId, secret: $apiKeySecret) {
                  jwt
                }
              }
            """
            payload = {
                "query": query,
                "variables": {
                    "apiKeyId": self._config.get("api.api_key_id"),
                    "apiKeySecret": self._config.get("api.api_key_secret"),
                },
            }

            response = requests.post(
                json=payload,
                url=self._config.get("api.api_key_endpoint"),
            )
            data = benedict(response.json())

            if "errors" in data:
                raise RuntimeError(f"Spacelift API Error: {data.get('errors[0].message')}")

            self._api_jwt_token = data.get("data.apiKeyUser.jwt")

        return self._api_jwt_token

    def _get_sensitive_env_vars(self) -> list[dict]:
        env_vars = []

        data = load_normalized_data()
        for env_var in data.get("stack_variables"):
            # We only consider sensitive variables here
            if not env_var.get("write_only"):
                continue

            if "-" in env_var.get("name"):
                logging.warning(
                    f"Sensitive environment variable '{env_var.get('name')}' has a dash in its name. Skipping."
                )
                continue

            if env_var.get("value") and "\n" in env_var.get("value"):
                logging.warning(
                    f"Sensitive environment variable '{env_var.get('name')}' has a '\\n' character in its value. "
                    "Skipping."
                )
                continue

            env_vars.append(env_var)

        return env_vars

    def _set_sensitive_env_var(self, env_var: dict) -> None:
        operation = """
          mutation UpdateStackConfig($stackId: ID!, $input: ConfigInput!) {
            stackConfigAdd(stack: $stackId, config: $input) {
              id
            }
          }
        """

        env_var_id = f"TF_VAR_{env_var.get('name')}" if env_var.get("type") == "terraform" else env_var.get("name")

        variables = {
            "stackId": env_var.get("_relationships.stack.slug"),
            "input": {
                "id": env_var_id,
                "type": "ENVIRONMENT_VARIABLE",
                "value": env_var.get("value"),
                "writeOnly": True,
            },
        }

        response = self._call_api(operation=operation, variables=variables)

        if response.get("errors"):
            logging.warning(
                "Error setting sensitive environment variable "
                f"'{env_var.get('_relationships.stack.slug')}/{env_var_id}': "
                f"{response.get('errors[0].message')}"
            )

    def _create_module_version(self, commit_sha: str, module: str, version: str) -> None:
        operation = """
          mutation CreateModuleVersion($moduleId: ID!, $commitSha: String, $version: String) {
            versionCreate(module: $moduleId, commitSha: $commitSha, version: $version) {
              id
            }
          }
        """

        variables = {
            "commitSha": commit_sha,
            "moduleId": module,
            "version": version,
        }

        self._call_api(operation=operation, variables=variables)

    def _get_module_versions(self, module: str) -> list:
        versions = {}

        operation = """
          query GetModuleVersions($moduleId: ID!, $before: ID, $includeFailed: Boolean) {
            module(id: $moduleId) {
              id
              versions(before: $before, includeFailed: $includeFailed) {
                commit {
                  hash
                }
                number
              }
            }
          }
        """

        variables = {
            "includeFailed": False,
            "moduleId": module,
        }

        response = self._call_api(operation=operation, variables=variables)
        for version in response.get("data.module.versions"):
            versions[version["number"]] = version["commit"]["hash"]

        return versions

    def _get_stacks_with_invalid_env_var_names(self) -> list:
        data = load_normalized_data()

        return [stack for stack in data.get("stacks") if stack.get("has_variables_with_invalid_name") is True]

    def _get_terraform_var_with_invalid_name_for_stack(self, stack_source_id: str) -> list:
        data = load_normalized_data()

        return [
            var
            for var in data.get("stack_variables")
            if var.get("_relationships.stack._source_id") == stack_source_id
            and var.get("type") == "terraform"
            and var.get("valid_name") is False
        ]

    def create_module_version(self, commit_sha: str, module: str, version: str):
        versions = self._get_module_versions(module=module)

        if version in versions:
            logging.info(f"Version '{version}' of module '{module}' already exists. Skipping.")
        else:
            self._create_module_version(commit_sha=commit_sha, module=module, version=version)
            logging.debug(f"Created version '{version}' using commit '{commit_sha}' for module '{module}'")

    def _set_mounted_file_content(self, content: str, filename: str, stack_id: str, write_only: bool = False) -> None:
        operation = """
          mutation UpdateStackConfig($stackId: ID!, $input: ConfigInput!) {
            stackConfigAdd(stack: $stackId, config: $input) {
              id
            }
          }
        """

        variables = {
            "stackId": stack_id,
            "input": {
                "id": filename,
                "type": "FILE_MOUNT",
                "value": b64encode(content.encode()).decode(),
                "writeOnly": write_only,
            },
        }

        response = self._call_api(operation=operation, variables=variables)

        if response.get("errors"):
            logging.warning(
                f"Error setting mounted file '{filename}' for stack '{stack_id}': "
                f"{response.get('errors[0].message')}"
            )

    def set_sensitive_env_vars(self) -> None:
        env_vars = self._get_sensitive_env_vars()
        for env_var in env_vars:
            if env_var.get("value"):
                self._set_sensitive_env_var(env_var)
            else:
                logging.debug(
                    f"No value for '{env_var.get('_relationships.stack.slug')}/{env_var.get('name')}' "
                    "sensitive environment variable. Skipping."
                )

    def set_terraform_vars_with_invalid_name(self) -> None:
        for stack in self._get_stacks_with_invalid_env_var_names():
            plain_mounted_file_content = ""
            secret_mounted_file_content = ""
            for env_var in self._get_terraform_var_with_invalid_name_for_stack(stack_source_id=stack.get("_source_id")):
                if env_var.get("hcl"):
                    new_line = f"{env_var.get('name')} = {env_var.get('value')}\n"
                else:
                    new_line = f"{env_var.get('name')} = \"{env_var.get('value')}\"\n"

                if env_var.get("write_only"):
                    secret_mounted_file_content += new_line
                else:
                    plain_mounted_file_content += new_line

            self._set_mounted_file_content(
                content=plain_mounted_file_content,
                filename=os.path.normpath(
                    f"source/{stack.get('vcs.project_root')}/tf_vars_with_invalid_name.auto.tfvars"
                ),
                stack_id=stack.get("slug"),
            )

            self._set_mounted_file_content(
                content=secret_mounted_file_content,
                filename=os.path.normpath(
                    f"source/{stack.get('vcs.project_root')}/tf_secret_vars_with_invalid_name.auto.tfvars"
                ),
                stack_id=stack.get("slug"),
                write_only=True,
            )
