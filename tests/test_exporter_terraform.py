# ruff: noqa: SLF001
import pytest

from spacemk.exporters import terraform


@pytest.mark.vcr()
def test_tfe_list_agent_pools(terraform_exporter: terraform.Exporter):
    terraform_exporter._list_agent_pools("org-example")


@pytest.mark.vcr()
def test_tfe_list_organization(terraform_exporter: terraform.Exporter):
    terraform_exporter._list_organizations()


@pytest.mark.vcr()
def test_tfe_list_policies(terraform_exporter: terraform.Exporter):
    terraform_exporter._list_policies("org-example")


@pytest.mark.vcr()
def test_tfe_list_policy_sets(terraform_exporter: terraform.Exporter):
    terraform_exporter._list_policy_sets("org-example")


@pytest.mark.vcr()
def test_tfe_list_projects(terraform_exporter: terraform.Exporter):
    terraform_exporter._list_projects("org-example")


@pytest.mark.vcr()
def test_tfe_list_registry_modules(terraform_exporter: terraform.Exporter):
    terraform_exporter._list_registry_modules("org-example")


@pytest.mark.vcr()
def test_tfe_list_registry_providers(terraform_exporter: terraform.Exporter):
    terraform_exporter._list_registry_providers("org-example")


@pytest.mark.vcr()
def test_tfe_list_tasks(terraform_exporter: terraform.Exporter):
    terraform_exporter._list_tasks("org-example")


@pytest.mark.vcr()
def test_tfe_list_teams(terraform_exporter: terraform.Exporter):
    terraform_exporter._list_teams("org-example")


@pytest.mark.vcr()
def test_tfe_list_variables(terraform_exporter: terraform.Exporter):
    terraform_exporter._list_variables("ws-example")


@pytest.mark.vcr()
def test_tfe_list_variable_sets(terraform_exporter: terraform.Exporter):
    terraform_exporter._list_variable_sets("org-example")


@pytest.mark.vcr()
def test_tfe_list_workspaces(terraform_exporter: terraform.Exporter):
    terraform_exporter._list_workspaces("org-example")
