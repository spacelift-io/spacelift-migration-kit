import click
import requests


class Importer:
    def __init__(self, config):
        self._config = config

        # self._api_token = self._get_api_token() # noqa: ERA001

    def _call_api(self, operation, variables=None):
        headers = {
            "Authorization": f"Bearer {self._api_token}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            headers=headers,
            json={"query": operation, "variables": variables},
            url=self._config["spacelift_api_key"]["endpoint"],
        )

        return response.json()

    def _get_api_token(self):
        mutation = """mutation GetSpaceliftToken($apiKeyId: ID!, $apiKeySecret: String!) {
                        apiKeyUser(id: $apiKeyId, secret: $apiKeySecret) {
                          jwt
                        }
                      }"""

        variables = {
            "apiKeyId": self._config.get("spacelift_api_key.id"),
            "apiKeySecret": self._config.get("spacelift_api_key.secret"),
        }

        response = requests.post(
            self._config.get("spacelift_api_key.endpoint"),
            json={"query": mutation, "variables": variables},
        )

        return response.json()["data"]["apiKeyUser"]["jwt"]

    def _trigger_manager_stack(self, stack_id: str):
        """Trigger Spacelift manager stack to create entities"""
        mutation = """mutation TriggerRun($stackId: ID!) {
                        runTrigger(stack: $stackId) {
                          id
                        }
                      }"""

        variables = {"stackId": stack_id}

        self._call_api(mutation, variables=variables)

    def _create_manager_stack(self) -> str:
        """Create Spacelift manager stack"""
        mutation = """mutation CreateStack($input: StackInput!, $manageState: Boolean!) {
                        stackCreate(input: $input, manageState: $manageState) {
                          id
                        }
                      }"""

        vcs_user, vcs_repository = self._config.get("manager_stack.vcs.repository").split("/")
        variables = {
            "input": {
                "administrative": True,
                "branch": self._config.get("manager_stack.vcs.branch"),
                "description": self._config.get("manager_stack.description"),
                "githubActionDeploy": False,
                "labels": self._config.get("manager_stack.labels"),
                "localPreviewEnabled": True,
                "name": self._config.get("manager_stack.name"),
                "namespace": vcs_user,
                "projectRoot": self._config.get("manager_stack.vcs.project_root"),
                "provider": self._config.get("manager_stack.vcs.provider").upper(),
                "repository": vcs_repository,
                "space": "root",
                "vendorConfig": {
                    "terraform": {
                        "version": self._config.get("manager_stack.vendor.version"),
                        "workflowTool": "TERRAFORM_FOSS",
                        "useSmartSanitization": True,
                    }
                },
            },
            "manageState": True,
        }
        data = self._call_api(mutation, variables=variables)

        return data["data"]["stackCreate"]["id"]

    def create(self):
        """Create Spacelift manager stack and entities"""
        # manager_stack_id = self._create_manager_stack() # noqa: ERA001
        # self._trigger_manager_stack(manager_stack_id) # noqa: ERA001
        click.echo(
            "Once the generated code has been pushed to a git repository, create an administrative Spacelift stack"
            " in the 'root' space that points to the repository."
            "It will create all the other Spacelift resources."
        )
