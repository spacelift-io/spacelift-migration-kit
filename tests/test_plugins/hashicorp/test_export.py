"""Tests for HashiCorp plugin smk_export_data hook."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

if TYPE_CHECKING:
    from pathlib import Path

import orjson
import pytest
from pytfe.models import Organization, Project, Workspace

from smk.plugins.hashicorp import smk_audit_entity_type, smk_export_data, smk_get_entity_types


@pytest.fixture
def vendor_config() -> dict[str, Any]:
    return {"credentials": {"product": "hcp_terraform", "token": "test-token"}, "source_plugin": "hashicorp"}


@pytest.fixture
def tfe_vendor_config() -> dict[str, Any]:
    return {
        "credentials": {
            "product": "terraform_enterprise",
            "tfe_hostname": "https://terraform.example.com",
            "token": "test-token",
        },
        "source_plugin": "hashicorp",
    }


@pytest.fixture
def mock_organizations() -> list[Organization]:
    return [
        Organization(id="org-1", name="org-one", email="admin@org-one.example.com"),
        Organization(id="org-2", name="org-two", email="admin@org-two.example.com"),
    ]


@pytest.fixture
def mock_projects() -> dict[str, list[Project]]:
    return {
        "org-one": [
            Project(id="prj-1", name="Default Project", organization="org-one"),
            Project(id="prj-2", name="Project Alpha", organization="org-one"),
        ],
        "org-two": [
            Project(id="prj-3", name="Default Project", organization="org-two"),
        ],
    }


@pytest.fixture
def mock_workspaces() -> dict[str, list[Workspace]]:
    return {
        "org-one": [
            Workspace(id="ws-1", name="workspace-a", organization="org-one"),
            Workspace(id="ws-2", name="workspace-b", organization="org-one"),
        ],
        "org-two": [
            Workspace(id="ws-3", name="workspace-c", organization="org-two"),
        ],
    }


def _make_client(
    organizations: list[Organization],
    projects: dict[str, list[Project]],
    workspaces: dict[str, list[Workspace]],
) -> MagicMock:
    client = MagicMock()
    client.organizations.list.return_value = iter(organizations)
    client.projects.list.side_effect = lambda org_name: iter(projects.get(org_name, []))
    client.workspaces.list.side_effect = lambda org_name: iter(workspaces.get(org_name, []))
    return client


def test_export_returns_correct_counts(
    tmp_path: Path,
    vendor_config: dict[str, Any],
    mock_organizations: list[Organization],
    mock_projects: dict[str, list[Project]],
    mock_workspaces: dict[str, list[Workspace]],
) -> None:
    client = _make_client(mock_organizations, mock_projects, mock_workspaces)
    with (
        patch("smk.plugins.hashicorp.TFEClient", return_value=client),
        patch("smk.plugins.hashicorp.get_data_dir", return_value=tmp_path),
    ):
        result = smk_export_data(vendor_config)

    assert result == {"organizations": 2, "projects": 3, "workspaces": 3}


def test_export_writes_json_files(
    tmp_path: Path,
    vendor_config: dict[str, Any],
    mock_organizations: list[Organization],
    mock_projects: dict[str, list[Project]],
    mock_workspaces: dict[str, list[Workspace]],
) -> None:
    client = _make_client(mock_organizations, mock_projects, mock_workspaces)
    with (
        patch("smk.plugins.hashicorp.TFEClient", return_value=client),
        patch("smk.plugins.hashicorp.get_data_dir", return_value=tmp_path),
    ):
        smk_export_data(vendor_config)

    assert (tmp_path / "organizations.json").exists()
    assert (tmp_path / "projects.json").exists()
    assert (tmp_path / "workspaces.json").exists()


def test_export_written_files_are_valid_json(
    tmp_path: Path,
    vendor_config: dict[str, Any],
    mock_organizations: list[Organization],
    mock_projects: dict[str, list[Project]],
    mock_workspaces: dict[str, list[Workspace]],
) -> None:
    client = _make_client(mock_organizations, mock_projects, mock_workspaces)
    with (
        patch("smk.plugins.hashicorp.TFEClient", return_value=client),
        patch("smk.plugins.hashicorp.get_data_dir", return_value=tmp_path),
    ):
        smk_export_data(vendor_config)

    orgs_raw = orjson.loads((tmp_path / "organizations.json").read_bytes())
    projects_raw = orjson.loads((tmp_path / "projects.json").read_bytes())
    workspaces_raw = orjson.loads((tmp_path / "workspaces.json").read_bytes())

    assert len(orgs_raw) == 2
    assert len(projects_raw) == 3
    assert len(workspaces_raw) == 3


def test_export_round_trips_models(
    tmp_path: Path,
    vendor_config: dict[str, Any],
    mock_organizations: list[Organization],
    mock_projects: dict[str, list[Project]],
    mock_workspaces: dict[str, list[Workspace]],
) -> None:
    client = _make_client(mock_organizations, mock_projects, mock_workspaces)
    with (
        patch("smk.plugins.hashicorp.TFEClient", return_value=client),
        patch("smk.plugins.hashicorp.get_data_dir", return_value=tmp_path),
    ):
        smk_export_data(vendor_config)

    loaded_orgs = [Organization.model_validate(d) for d in orjson.loads((tmp_path / "organizations.json").read_bytes())]
    loaded_projects = [Project.model_validate(d) for d in orjson.loads((tmp_path / "projects.json").read_bytes())]
    loaded_workspaces = [Workspace.model_validate(d) for d in orjson.loads((tmp_path / "workspaces.json").read_bytes())]

    assert loaded_orgs == mock_organizations
    assert loaded_projects == [p for ps in mock_projects.values() for p in ps]
    assert loaded_workspaces == [w for ws in mock_workspaces.values() for w in ws]


def test_export_uses_tfe_hostname_for_enterprise(
    tmp_path: Path,
    tfe_vendor_config: dict[str, Any],
    mock_organizations: list[Organization],
    mock_projects: dict[str, list[Project]],
    mock_workspaces: dict[str, list[Workspace]],
) -> None:
    client = _make_client(mock_organizations, mock_projects, mock_workspaces)
    captured: list[Any] = []

    def capture_config(config: Any) -> MagicMock:
        captured.append(config)
        return client

    with (
        patch("smk.plugins.hashicorp.TFEClient", side_effect=capture_config),
        patch("smk.plugins.hashicorp.get_data_dir", return_value=tmp_path),
    ):
        smk_export_data(tfe_vendor_config)

    assert len(captured) == 1
    assert captured[0].address == "https://terraform.example.com"
    assert captured[0].token == "test-token"


def test_export_uses_hcp_address_for_hcp_terraform(
    tmp_path: Path,
    vendor_config: dict[str, Any],
    mock_organizations: list[Organization],
    mock_projects: dict[str, list[Project]],
    mock_workspaces: dict[str, list[Workspace]],
) -> None:
    client = _make_client(mock_organizations, mock_projects, mock_workspaces)
    captured: list[Any] = []

    def capture_config(config: Any) -> MagicMock:
        captured.append(config)
        return client

    with (
        patch("smk.plugins.hashicorp.TFEClient", side_effect=capture_config),
        patch("smk.plugins.hashicorp.get_data_dir", return_value=tmp_path),
    ):
        smk_export_data(vendor_config)

    assert captured[0].address == "https://app.terraform.io"


def test_export_empty_org_list(
    tmp_path: Path,
    vendor_config: dict[str, Any],
) -> None:
    client = _make_client([], {}, {})
    with (
        patch("smk.plugins.hashicorp.TFEClient", return_value=client),
        patch("smk.plugins.hashicorp.get_data_dir", return_value=tmp_path),
    ):
        result = smk_export_data(vendor_config)

    assert result == {"organizations": 0, "projects": 0, "workspaces": 0}
    assert orjson.loads((tmp_path / "organizations.json").read_bytes()) == []


def test_export_auth_error_raises_smk_error_with_guidance(
    tmp_path: Path,
    vendor_config: dict[str, Any],
) -> None:
    from pytfe.errors import AuthError

    from smk.core.exceptions import SMKError

    client = MagicMock()
    client.organizations.list.side_effect = AuthError("unauthorized")
    with (
        patch("smk.plugins.hashicorp.TFEClient", return_value=client),
        patch("smk.plugins.hashicorp.get_data_dir", return_value=tmp_path),
        pytest.raises(SMKError, match="Configure page"),
    ):
        smk_export_data(vendor_config)


def test_export_network_error_raises_smk_error_with_guidance(
    tmp_path: Path,
    vendor_config: dict[str, Any],
) -> None:
    from smk.core.exceptions import SMKError

    client = MagicMock()
    client.organizations.list.side_effect = ConnectionError("timed out")
    with (
        patch("smk.plugins.hashicorp.TFEClient", return_value=client),
        patch("smk.plugins.hashicorp.get_data_dir", return_value=tmp_path),
        pytest.raises(SMKError, match="network connection"),
    ):
        smk_export_data(vendor_config)


def test_export_skips_non_hashicorp_source(vendor_config: dict[str, Any]) -> None:
    """smk_export_data returns None when source_plugin != 'hashicorp'."""
    config = dict(vendor_config)
    config["source_plugin"] = "other"
    result = smk_export_data(config)
    assert result is None


def test_export_get_source_info_structure() -> None:
    """smk_get_source_info returns expected keys."""
    from smk.plugins.hashicorp import smk_get_source_info

    info = smk_get_source_info()
    assert info["plugin_id"] == "hashicorp"
    assert "display_name" in info
    assert "fields" in info


def test_export_rate_limited_raises_smk_error(
    tmp_path: Path,
    vendor_config: dict[str, Any],
) -> None:
    from pytfe.errors import RateLimited

    from smk.core.exceptions import SMKError

    client = MagicMock()
    exc = RateLimited("rate limited")
    exc.retry_after = 30
    client.organizations.list.side_effect = exc
    with (
        patch("smk.plugins.hashicorp.TFEClient", return_value=client),
        patch("smk.plugins.hashicorp.get_data_dir", return_value=tmp_path),
        pytest.raises(SMKError, match="Rate limited"),
    ):
        smk_export_data(vendor_config)


def test_export_server_error_raises_smk_error(
    tmp_path: Path,
    vendor_config: dict[str, Any],
) -> None:
    from pytfe.errors import ServerError

    from smk.core.exceptions import SMKError

    client = MagicMock()
    client.organizations.list.side_effect = ServerError("500 internal")
    with (
        patch("smk.plugins.hashicorp.TFEClient", return_value=client),
        patch("smk.plugins.hashicorp.get_data_dir", return_value=tmp_path),
        pytest.raises(SMKError, match="server error"),
    ):
        smk_export_data(vendor_config)


def test_export_tfe_error_raises_smk_error(
    tmp_path: Path,
    vendor_config: dict[str, Any],
) -> None:
    from pytfe.errors import TFEError

    from smk.core.exceptions import SMKError

    client = MagicMock()
    client.organizations.list.side_effect = TFEError("generic tfe error")
    with (
        patch("smk.plugins.hashicorp.TFEClient", return_value=client),
        patch("smk.plugins.hashicorp.get_data_dir", return_value=tmp_path),
        pytest.raises(SMKError, match="API error"),
    ):
        smk_export_data(vendor_config)


def test_export_org_with_no_name_raises_value_error(
    tmp_path: Path,
    vendor_config: dict[str, Any],
) -> None:
    from pytfe.models import Organization

    org = Organization(id="org-no-name", name=None, email="x@x.com")
    client = MagicMock()
    client.organizations.list.return_value = iter([org])
    with (
        patch("smk.plugins.hashicorp.TFEClient", return_value=client),
        patch("smk.plugins.hashicorp.get_data_dir", return_value=tmp_path),
        pytest.raises(ValueError, match="no name"),
    ):
        smk_export_data(vendor_config)


# --- smk_get_entity_types ---


def test_get_entity_types_returns_three_types_for_hashicorp() -> None:
    result = smk_get_entity_types(source_plugin="hashicorp")
    assert result is not None
    ids = [et["id"] for et in result]
    assert ids == ["organizations", "projects", "workspaces"]


def test_get_entity_types_returns_none_for_other_plugin() -> None:
    result = smk_get_entity_types(source_plugin="other")
    assert result is None


def test_get_entity_types_each_has_display_name() -> None:
    result = smk_get_entity_types(source_plugin="hashicorp")
    assert result is not None
    for et in result:
        assert "display_name" in et
        assert et["display_name"]


# --- smk_audit_entity_type ---


def test_audit_returns_none_for_other_plugin() -> None:
    result = smk_audit_entity_type(entity_type="workspaces", entities=[], source_plugin="other")
    assert result is None


def test_audit_returns_empty_list_for_organizations() -> None:
    result = smk_audit_entity_type(entity_type="organizations", entities=[], source_plugin="hashicorp")
    assert result == []


def test_audit_workspaces_no_resources_warning() -> None:
    ws = {"id": "ws-1", "attributes": {"resource-count": 0, "vcs-repo": {"identifier": "org/repo"}}}
    result = smk_audit_entity_type(entity_type="workspaces", entities=[ws], source_plugin="hashicorp")
    assert result is not None
    assert any(i["severity"] == "warning" and "No resources" in i["message"] for i in result)


def test_audit_workspaces_no_vcs_warning() -> None:
    ws = {"id": "ws-2", "attributes": {"resource-count": 5, "vcs-repo": None}}
    result = smk_audit_entity_type(entity_type="workspaces", entities=[ws], source_plugin="hashicorp")
    assert result is not None
    assert any("No VCS" in i["message"] for i in result)


def test_audit_workspaces_clean_workspace_no_issues() -> None:
    entities = [{"id": "ws-3", "attributes": {"resource-count": 2, "vcs-repo": {"identifier": "org/repo"}}}]
    result = smk_audit_entity_type(entity_type="workspaces", entities=entities, source_plugin="hashicorp")
    assert result == []


def test_audit_workspaces_both_issues_on_same_workspace() -> None:
    ws = {"id": "ws-4", "attributes": {"resource-count": 0, "vcs-repo": None}}
    result = smk_audit_entity_type(entity_type="workspaces", entities=[ws], source_plugin="hashicorp")
    assert result is not None
    assert len(result) == 2
    assert all(i["entity_id"] == "ws-4" for i in result)


def test_audit_issues_include_entity_data() -> None:
    ws = {"id": "ws-5", "attributes": {"resource-count": 0, "vcs-repo": None}}
    result = smk_audit_entity_type(entity_type="workspaces", entities=[ws], source_plugin="hashicorp")
    assert result is not None
    assert all(i["entity"] == ws for i in result)


def test_audit_projects_no_name_error() -> None:
    entities = [{"id": "prj-1", "attributes": {}}]
    result = smk_audit_entity_type(entity_type="projects", entities=entities, source_plugin="hashicorp")
    assert result is not None
    assert any(i["severity"] == "error" and "No project name" in i["message"] for i in result)


def test_audit_projects_with_name_no_issues() -> None:
    entities = [{"id": "prj-2", "attributes": {"name": "My Project"}}]
    result = smk_audit_entity_type(entity_type="projects", entities=entities, source_plugin="hashicorp")
    assert result == []


def test_audit_projects_issue_includes_entity_data() -> None:
    project = {"id": "prj-3", "attributes": {}}
    result = smk_audit_entity_type(entity_type="projects", entities=[project], source_plugin="hashicorp")
    assert result is not None
    assert result[0]["entity"] == project
