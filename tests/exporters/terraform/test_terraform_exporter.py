# ruff: noqa: SLF001
import os
from unittest.mock import ANY

import pytest
from rich.console import Console

from spacemk.exporters import load_exporter, terraform


@pytest.fixture(scope="module")
def terraform_exporter():
    config = {
        "name": "terraform",
        "settings": {
            "api_endpoint": os.getenv("TF_API_ENDPOINT", "https://app.terraform.io"),
            "api_token": os.getenv("TF_API_TOKEN"),
            "include": {"organizations": "^smk-.*$"},
        },
    }

    return load_exporter(config=config, console=Console())


@pytest.mark.vcr()
def test_list_agent_pools(terraform_exporter: terraform.Exporter):
    expected = [
        {"attributes": {"id": ANY, "agent-count": 0, "name": "smk-agent-pool-1", "organization-scoped": True}},
        {"attributes": {"id": ANY, "agent-count": 0, "name": "smk-agent-pool-2", "organization-scoped": False}},
    ]

    actual_org_1 = terraform_exporter._list_agent_pools("smk-organization-1")
    assert actual_org_1 == expected

    actual_org_2 = terraform_exporter._list_agent_pools("smk-organization-2")
    assert actual_org_2 == expected

    actual_org_3 = terraform_exporter._list_agent_pools("smk-organization-3")
    assert actual_org_3 == expected


@pytest.mark.vcr()
def test_list_organization(terraform_exporter: terraform.Exporter):
    expected = [
        {"attributes": {"id": "smk-organization-1"}},
        {"attributes": {"id": "smk-organization-2"}},
        {"attributes": {"id": "smk-organization-3"}},
    ]
    actual = terraform_exporter._list_organizations()
    assert actual == expected


@pytest.mark.vcr()
def test_list_policies(terraform_exporter: terraform.Exporter):
    expected_org_1 = [
        {
            "attributes": {
                "id": ANY,
                "description": "SMK OPA policy #1",
                "enforcement-level": "advisory",
                "kind": "opa",
                "name": "smk-opa-policy-1",
            }
        },
        {
            "attributes": {
                "id": ANY,
                "description": "SMK OPA policy #2",
                "enforcement-level": "mandatory",
                "kind": "opa",
                "name": "smk-opa-policy-2",
            }
        },
    ]
    actual_org_1 = terraform_exporter._list_policies("smk-organization-1")
    assert actual_org_1 == expected_org_1

    expected_org_2 = [
        {
            "attributes": {
                "id": ANY,
                "description": "SMK Sentinel policy #1",
                "enforcement-level": "advisory",
                "kind": "sentinel",
                "name": "smk-sentinel-policy-1",
            }
        },
        {
            "attributes": {
                "id": ANY,
                "description": "SMK Sentinel policy #2",
                "enforcement-level": "hard-mandatory",
                "kind": "sentinel",
                "name": "smk-sentinel-policy-2",
            }
        },
    ]
    actual_org_2 = terraform_exporter._list_policies("smk-organization-2")
    assert actual_org_2 == expected_org_2

    expected_org_3 = [
        {
            "attributes": {
                "id": ANY,
                "description": "SMK Sentinel policy #1",
                "enforcement-level": "advisory",
                "kind": "sentinel",
                "name": "smk-sentinel-policy-1",
            }
        },
        {
            "attributes": {
                "id": ANY,
                "description": "SMK Sentinel policy #2",
                "enforcement-level": "soft-mandatory",
                "kind": "sentinel",
                "name": "smk-sentinel-policy-2",
            }
        },
    ]
    actual_org_3 = terraform_exporter._list_policies("smk-organization-3")
    assert actual_org_3 == expected_org_3


@pytest.mark.vcr()
def test_tfe_list_policy_sets(terraform_exporter: terraform.Exporter):
    expected_org_1 = [
        {
            "attributes": {
                "id": ANY,
                "description": "SMK OPA policy set #1",
                "global": False,
                "kind": "opa",
                "name": "smk-opa-policy-set-1",
            }
        }
    ]
    actual_org_1 = terraform_exporter._list_policy_sets("smk-organization-1")
    assert actual_org_1 == expected_org_1

    expected_org_2 = [
        {
            "attributes": {
                "id": ANY,
                "description": "SMK Sentinel policy set #1",
                "global": False,
                "kind": "sentinel",
                "name": "smk-sentinel-policy-set-1",
            }
        }
    ]
    actual_org_2 = terraform_exporter._list_policy_sets("smk-organization-2")
    assert actual_org_2 == expected_org_2

    expected_org_3 = [
        {
            "attributes": {
                "id": ANY,
                "description": "SMK Sentinel policy set #1",
                "global": False,
                "kind": "sentinel",
                "name": "smk-sentinel-policy-set-1",
            }
        }
    ]
    actual_org_3 = terraform_exporter._list_policy_sets("smk-organization-3")
    assert actual_org_3 == expected_org_3


@pytest.mark.vcr()
def test_tfe_list_projects(terraform_exporter: terraform.Exporter):
    expected_org_1 = [
        {"attributes": {"id": ANY, "name": "Default Project"}},
        {"attributes": {"id": ANY, "name": "smk-project-1"}},
        {"attributes": {"id": ANY, "name": "smk-project-2"}},
    ]
    actual_org_1 = terraform_exporter._list_projects("smk-organization-1")
    assert actual_org_1 == expected_org_1

    expected_org_2 = [
        {"attributes": {"id": ANY, "name": "Default Project"}},
        {"attributes": {"id": ANY, "name": "smk-project-1"}},
        {"attributes": {"id": ANY, "name": "smk-project-2"}},
    ]
    actual_org_2 = terraform_exporter._list_projects("smk-organization-2")
    assert actual_org_2 == expected_org_2

    expected_org_3 = [
        {"attributes": {"id": ANY, "name": "Default Project"}},
        {"attributes": {"id": ANY, "name": "smk-project-1"}},
        {"attributes": {"id": ANY, "name": "smk-project-2"}},
    ]
    actual_org_3 = terraform_exporter._list_projects("smk-organization-3")
    assert actual_org_3 == expected_org_3


@pytest.mark.vcr()
def test_tfe_list_registry_modules(terraform_exporter: terraform.Exporter):
    expected_org_1 = [
        {
            "attributes": {
                "id": ANY,
                "name": "example_module",
                "namespace": "smk-organization-1",
                "provider": "smk",
                "status": "pending",
            }
        },
        {
            "attributes": {
                "id": ANY,
                "name": "vpc",
                "namespace": "terraform-aws-modules",
                "provider": "aws",
                "status": "setup_complete",
            }
        },
    ]
    actual_org_1 = terraform_exporter._list_registry_modules("smk-organization-1")
    assert actual_org_1 == expected_org_1

    expected_org_2 = [
        {
            "attributes": {
                "id": ANY,
                "name": "example_module",
                "namespace": "smk-organization-2",
                "provider": "smk",
                "status": "pending",
            }
        },
        {
            "attributes": {
                "id": ANY,
                "name": "vpc",
                "namespace": "terraform-aws-modules",
                "provider": "aws",
                "status": "setup_complete",
            }
        },
    ]
    actual_org_2 = terraform_exporter._list_registry_modules("smk-organization-2")
    assert actual_org_2 == expected_org_2

    expected_org_3 = [
        {
            "attributes": {
                "id": ANY,
                "name": "example_module",
                "namespace": "smk-organization-3",
                "provider": "smk",
                "status": "pending",
            }
        },
        {
            "attributes": {
                "id": ANY,
                "name": "vpc",
                "namespace": "terraform-aws-modules",
                "provider": "aws",
                "status": "setup_complete",
            }
        },
    ]
    actual_org_3 = terraform_exporter._list_registry_modules("smk-organization-3")
    assert actual_org_3 == expected_org_3


@pytest.mark.skip(reason="Not implemented yet")
@pytest.mark.vcr()
def test_tfe_list_registry_providers(terraform_exporter: terraform.Exporter):
    expected_org_1 = []
    actual_org_1 = terraform_exporter._list_registry_providers("smk-organization-1")
    assert actual_org_1 == expected_org_1

    expected_org_2 = []
    actual_org_2 = terraform_exporter._list_registry_providers("smk-organization-2")
    assert actual_org_2 == expected_org_2

    expected_org_3 = []
    actual_org_3 = terraform_exporter._list_registry_providers("smk-organization-3")
    assert actual_org_3 == expected_org_3


@pytest.mark.skip(reason="Not implemented yet")
@pytest.mark.vcr()
def test_tfe_list_tasks(terraform_exporter: terraform.Exporter):
    expected_org_1 = []
    actual_org_1 = terraform_exporter._list_tasks("smk-organization-1")
    assert actual_org_1 == expected_org_1

    expected_org_2 = []
    actual_org_2 = terraform_exporter._list_tasks("smk-organization-2")
    assert actual_org_2 == expected_org_2

    expected_org_3 = []
    actual_org_3 = terraform_exporter._list_tasks("smk-organization-3")
    assert actual_org_3 == expected_org_3


@pytest.mark.vcr()
def test_tfe_list_teams(terraform_exporter: terraform.Exporter):
    expected_org_1 = [{"attributes": {"id": ANY, "name": "owners", "users-count": 1}}]
    actual_org_1 = terraform_exporter._list_teams("smk-organization-1")
    assert actual_org_1 == expected_org_1

    expected_org_2 = [{"attributes": {"id": ANY, "name": "owners", "users-count": 1}}]
    actual_org_2 = terraform_exporter._list_teams("smk-organization-2")
    assert actual_org_2 == expected_org_2

    expected_org_3 = [{"attributes": {"id": ANY, "name": "owners", "users-count": 1}}]
    actual_org_3 = terraform_exporter._list_teams("smk-organization-3")
    assert actual_org_3 == expected_org_3


@pytest.mark.vcr()
def test_tfe_list_variables(terraform_exporter: terraform.Exporter):
    expected_variables = [
        {
            "attributes": {
                "id": ANY,
                "category": "env",
                "description": "HCL environment variable",
                "hcl": True,
                "key": "sensitive_hcl_env_var",
                "sensitive": True,
            }
        },
        {
            "attributes": {
                "id": ANY,
                "category": "env",
                "description": "Simple environment variable",
                "hcl": False,
                "key": "env_var",
                "sensitive": False,
            }
        },
        {
            "attributes": {
                "id": ANY,
                "category": "env",
                "description": "Sensitive environment variable",
                "hcl": False,
                "key": "sensitive_env_var",
                "sensitive": True,
            }
        },
        {
            "attributes": {
                "id": ANY,
                "category": "env",
                "description": "HCL environment variable",
                "hcl": True,
                "key": "hcl_env_var",
                "sensitive": False,
            }
        },
    ]

    actual_variables_1 = terraform_exporter._list_variables("ws-AhqVk8CoCrtAf1qk")
    assert actual_variables_1 == []

    actual_variables_2 = terraform_exporter._list_variables("ws-kJpdEf9zNHR4PCqa")
    assert actual_variables_2 == expected_variables

    actual_variables_3 = terraform_exporter._list_variables("ws-Fwk2uepV1GCRjZ1u")
    assert actual_variables_3 == []

    actual_variables_4 = terraform_exporter._list_variables("ws-PriJg5gR27pd7GpA")
    assert actual_variables_4 == expected_variables

    actual_variables_5 = terraform_exporter._list_variables("ws-dUtvk1dSMJR37Afp")
    assert actual_variables_5 == []

    actual_variables_6 = terraform_exporter._list_variables("ws-ncC6dqgZ81QpBBGx")
    assert actual_variables_6 == expected_variables


@pytest.mark.vcr()
def test_tfe_list_variable_sets(terraform_exporter: terraform.Exporter):
    expected_org_1 = [
        {
            "attributes": {
                "id": ANY,
                "description": "SMK variable set #1",
                "global": True,
                "name": "smk-variable-set-1",
                "project-count": 0,
                "var-count": 2,
                "workspace-count": 0,
            }
        },
        {
            "attributes": {
                "id": ANY,
                "description": "SMK variable set #3",
                "global": False,
                "name": "smk-variable-set-3",
                "project-count": 0,
                "var-count": 1,
                "workspace-count": 2,
            }
        },
        {
            "attributes": {
                "id": ANY,
                "description": "SMK variable set #2",
                "global": False,
                "name": "smk-variable-set-2",
                "project-count": 0,
                "var-count": 1,
                "workspace-count": 1,
            }
        },
    ]
    actual_org_1 = terraform_exporter._list_variable_sets("smk-organization-1")
    assert actual_org_1 == expected_org_1

    expected_org_2 = [
        {
            "attributes": {
                "id": ANY,
                "description": "SMK variable set #2",
                "global": False,
                "name": "smk-variable-set-2",
                "project-count": 0,
                "var-count": 1,
                "workspace-count": 1,
            }
        },
        {
            "attributes": {
                "id": ANY,
                "description": "SMK variable set #1",
                "global": True,
                "name": "smk-variable-set-1",
                "project-count": 0,
                "var-count": 2,
                "workspace-count": 0,
            }
        },
        {
            "attributes": {
                "id": ANY,
                "description": "SMK variable set #3",
                "global": False,
                "name": "smk-variable-set-3",
                "project-count": 0,
                "var-count": 1,
                "workspace-count": 2,
            }
        },
    ]
    actual_org_2 = terraform_exporter._list_variable_sets("smk-organization-2")
    assert actual_org_2 == expected_org_2

    expected_org_3 = [
        {
            "attributes": {
                "id": ANY,
                "description": "SMK variable set #3",
                "global": False,
                "name": "smk-variable-set-3",
                "project-count": 0,
                "var-count": 1,
                "workspace-count": 2,
            }
        },
        {
            "attributes": {
                "id": ANY,
                "description": "SMK variable set #1",
                "global": True,
                "name": "smk-variable-set-1",
                "project-count": 0,
                "var-count": 2,
                "workspace-count": 0,
            }
        },
        {
            "attributes": {
                "id": ANY,
                "description": "SMK variable set #2",
                "global": False,
                "name": "smk-variable-set-2",
                "project-count": 0,
                "var-count": 1,
                "workspace-count": 1,
            }
        },
    ]
    actual_org_3 = terraform_exporter._list_variable_sets("smk-organization-3")
    assert actual_org_3 == expected_org_3


@pytest.mark.vcr()
def test_tfe_list_workspaces(terraform_exporter: terraform.Exporter):
    expected_org_1 = [
        {
            "attributes": {
                "id": ANY,
                "auto-apply": True,
                "description": "SMK Workspace #2",
                "name": "smk-workspace-2",
                "resource-count": 0,
                "terraform-version": "0.12.0",
                "working-directory": "",
            }
        },
        {
            "attributes": {
                "id": ANY,
                "auto-apply": False,
                "description": "SMK Workspace #1",
                "name": "smk-workspace-1",
                "resource-count": 0,
                "terraform-version": ">= 1.2.0",
                "working-directory": "",
            }
        },
    ]
    actual_org_1 = terraform_exporter._list_workspaces("smk-organization-1")
    assert actual_org_1 == expected_org_1

    expected_org_2 = [
        {
            "attributes": {
                "id": ANY,
                "auto-apply": True,
                "description": "SMK Workspace #2",
                "name": "smk-workspace-2",
                "resource-count": 0,
                "terraform-version": "0.12.0",
                "working-directory": "",
            }
        },
        {
            "attributes": {
                "id": ANY,
                "auto-apply": False,
                "description": "SMK Workspace #1",
                "name": "smk-workspace-1",
                "resource-count": 0,
                "terraform-version": ">= 1.2.0",
                "working-directory": "",
            }
        },
    ]
    actual_org_2 = terraform_exporter._list_workspaces("smk-organization-2")
    assert actual_org_2 == expected_org_2

    expected_org_3 = [
        {
            "attributes": {
                "id": ANY,
                "auto-apply": True,
                "description": "SMK Workspace #2",
                "name": "smk-workspace-2",
                "resource-count": 0,
                "terraform-version": "0.12.0",
                "working-directory": "",
            }
        },
        {
            "attributes": {
                "id": ANY,
                "auto-apply": False,
                "description": "SMK Workspace #1",
                "name": "smk-workspace-1",
                "resource-count": 0,
                "terraform-version": ">= 1.2.0",
                "working-directory": "",
            }
        },
    ]
    actual_org_3 = terraform_exporter._list_workspaces("smk-organization-3")
    assert actual_org_3 == expected_org_3
