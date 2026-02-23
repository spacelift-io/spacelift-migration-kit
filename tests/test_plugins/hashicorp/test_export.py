"""Tests for HashiCorp plugin smk_export_data hook."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

if TYPE_CHECKING:
    from pathlib import Path

import orjson
import pytest
from pytfe.models import Organization, Project, Workspace

from smk.plugins.hashicorp import smk_export_data


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
