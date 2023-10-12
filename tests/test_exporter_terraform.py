# ruff: noqa: SLF001
import pytest

from spacemk.exporters import terraform


@pytest.mark.vcr()
def test_tfe_agent_pools(terraform_exporter: terraform.Exporter):
    terraform_exporter._list_agent_pools("org-example")


@pytest.mark.vcr()
def test_tfe_organization(terraform_exporter: terraform.Exporter):
    organizations = terraform_exporter._list_organizations()
    assert len(organizations) == 1
    assert organizations[0]["attributes"]["id"] == "org-example"


@pytest.mark.vcr()
def test_tfe_policies(terraform_exporter: terraform.Exporter):
    terraform_exporter._list_policies("org-example")


@pytest.mark.vcr()
def test_tfe_policy_sets(terraform_exporter: terraform.Exporter):
    terraform_exporter._list_policy_sets("org-example")


@pytest.mark.vcr()
def test_tfe_projects(terraform_exporter: terraform.Exporter):
    terraform_exporter._list_projects("org-example")


@pytest.mark.vcr()
def test_tfe_registry_modules(terraform_exporter: terraform.Exporter):
    terraform_exporter._list_registry_modules("org-example")


@pytest.mark.vcr()
def test_tfe_registry_providers(terraform_exporter: terraform.Exporter):
    terraform_exporter._list_registry_providers("org-example")


@pytest.mark.vcr()
def test_tfe_tasks(terraform_exporter: terraform.Exporter):
    terraform_exporter._list_tasks("org-example")


@pytest.mark.vcr()
def test_tfe_teams(terraform_exporter: terraform.Exporter):
    terraform_exporter._list_teams("org-example")


@pytest.mark.vcr()
def test_tfe_variables(terraform_exporter: terraform.Exporter):
    terraform_exporter._list_variables("ws-example")


@pytest.mark.vcr()
def test_tfe_variable_sets(terraform_exporter: terraform.Exporter):
    terraform_exporter._list_variable_sets("org-example")


@pytest.mark.vcr()
def test_tfe_workspaces(terraform_exporter: terraform.Exporter):
    terraform_exporter._list_workspaces("org-example")
