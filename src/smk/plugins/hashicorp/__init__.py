"""HashiCorp source plugin for SMK.

Supports both HCP Terraform (formerly Terraform Cloud) and self-hosted
Terraform Enterprise. The distinction is controlled by the `product` field.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

import orjson
import pluggy
from pytfe import TFEClient, TFEConfig
from pytfe.errors import AuthError, RateLimited, ServerError, TFEError

from smk.core.config.paths import get_data_dir
from smk.core.exceptions import SMKError

if TYPE_CHECKING:
    from pathlib import Path

    from pydantic import BaseModel

hookimpl = pluggy.HookimplMarker("smk")

HCP_TF_ADDRESS = "https://app.terraform.io"

PRODUCT_OPTIONS = [
    {"label": "HCP Terraform (Terraform Cloud)", "value": "hcp_terraform"},
    {"label": "Terraform Enterprise (self-hosted)", "value": "terraform_enterprise"},
]

logger = logging.getLogger(__name__)


def _write(path: Path, items: list[BaseModel]) -> None:
    data = [item.model_dump(by_alias=True) for item in items]
    path.write_bytes(orjson.dumps(data, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS))


@hookimpl
def smk_get_source_info() -> dict[str, Any]:
    """Return source plugin metadata for the configure UI."""
    return {
        "plugin_id": "hashicorp",
        "display_name": "HashiCorp",
        "description": "Migrate from HCP Terraform or self-hosted Terraform Enterprise.",
        "fields": [
            {
                "key": "product",
                "label": "Product",
                "type": "select",
                "required": True,
                "options": PRODUCT_OPTIONS,
                "help_text": "Choose your HashiCorp product.",
            },
            {
                "key": "tfe_hostname",
                "label": "Terraform Enterprise Hostname",
                "type": "url",
                "required": True,
                "depends_on": {"field": "product", "value": "terraform_enterprise"},
                "placeholder": "https://terraform.example.com",
                "help_text": "Base URL of your Terraform Enterprise instance.",
            },
            {
                "key": "token",
                "label": "API Token",
                "type": "password",
                "required": True,
                "placeholder": "",
                "help_text": "User or team API token with read access.",
            },
        ],
    }


@hookimpl
def smk_get_entity_types(source_plugin: str) -> list[dict] | None:
    """Return entity types exported by the HashiCorp plugin."""
    if source_plugin != "hashicorp":
        return None
    return [
        {"id": "organizations", "display_name": "Organizations"},
        {"id": "projects", "display_name": "Projects"},
        {"id": "workspaces", "display_name": "Workspaces"},
    ]


@hookimpl
def smk_audit_entity_type(
    entity_type: str,
    entities: list[dict],
    source_plugin: str,
) -> list[dict] | None:
    """Audit entities of a given type for HashiCorp plugin."""
    if source_plugin != "hashicorp":
        return None
    if entity_type == "workspaces":
        return _audit_workspaces(entities)
    if entity_type == "projects":
        return _audit_projects(entities)
    return []


def _audit_projects(entities: list[dict]) -> list[dict]:
    issues = []
    for project in entities:
        project_id = project.get("id", "unknown")
        if not project.get("attributes", {}).get("name"):
            issues.append(
                {"entity_id": project_id, "entity": project, "severity": "error", "message": "No project name"}
            )
    return issues


def _audit_workspaces(entities: list[dict]) -> list[dict]:
    issues = []
    for ws in entities:
        ws_id = ws.get("id", "unknown")
        if ws.get("attributes", {}).get("resource-count", 1) == 0:
            issues.append({"entity_id": ws_id, "entity": ws, "severity": "warning", "message": "No resources"})
        if not ws.get("attributes", {}).get("vcs-repo"):
            issues.append({"entity_id": ws_id, "entity": ws, "severity": "warning", "message": "No VCS configuration"})
    return issues


def _resource_name(name: str) -> str:
    """Sanitize a name into a valid Terraform resource identifier."""
    s = re.sub(r"[^a-z0-9]", "_", name.lower())
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "unknown"


def _entity_name(entity: dict[str, Any]) -> str:
    """Extract display name from entity."""
    return entity.get("name") or entity.get("attributes", {}).get("name") or entity.get("id", "")


@hookimpl
def smk_transform_entity(
    entity_type: str,
    entity: dict[str, Any],
    source_plugin: str,
) -> dict[str, Any] | None:
    """Transform a HashiCorp source entity into a Spacelift resource dict."""
    if source_plugin != "hashicorp":
        return None

    name = _entity_name(entity)
    parent_hcl = entity.get("_smk_parent_hcl_resource_name")

    if entity_type == "organizations":
        return {
            "resource_type": "spacelift_space",
            "resource_name": _resource_name(name),
            "attributes": {
                "name": name,
                "parent_space_id": "root",
            },
        }

    if entity_type == "projects":
        attrs: dict[str, Any] = {"name": name}
        if parent_hcl:
            attrs["parent_space_id"] = f"$ref:{parent_hcl}.id"
            parent_qualifier = parent_hcl.split(".", 1)[-1]
            proj_resource_name = _resource_name(f"{parent_qualifier}_{name}")
        else:
            attrs["parent_space_id"] = "root"
            proj_resource_name = _resource_name(name)
        return {
            "resource_type": "spacelift_space",
            "resource_name": proj_resource_name,
            "attributes": attrs,
        }

    if entity_type == "workspaces":
        # pytfe exports fields at the top level; JSON API format nests them under "attributes"
        raw = entity.get("attributes", entity)

        ws_attrs: dict[str, Any] = {"name": name}

        if parent_hcl:
            ws_attrs["space_id"] = f"$ref:{parent_hcl}.id"

        description = raw.get("description") or raw.get("description")
        if description:
            ws_attrs["description"] = description

        auto_apply = raw.get("auto_apply") if "auto_apply" in raw else raw.get("auto-apply")
        if auto_apply is not None:
            ws_attrs["autodeploy"] = auto_apply

        tf_version = raw.get("terraform_version") or raw.get("terraform-version")
        if tf_version:
            ws_attrs["terraform_version"] = tf_version

        working_dir = (raw.get("working_directory") or raw.get("working-directory") or "").rstrip("/")
        if working_dir:
            ws_attrs["project_root"] = working_dir

        vcs_repo = entity.get("vcs_repo") or entity.get("vcs-repo") or raw.get("vcs-repo")
        if vcs_repo:
            identifier = vcs_repo.get("identifier", "")
            if "/" in identifier:
                ws_attrs["namespace"], ws_attrs["repository"] = identifier.split("/", 1)
            elif identifier:
                ws_attrs["repository"] = identifier
            branch = vcs_repo.get("branch") or ""
            if branch:
                ws_attrs["branch"] = branch

        labels = raw.get("tag_names") or raw.get("tag-names") or []
        if labels:
            ws_attrs["labels"] = labels

        if parent_hcl:
            parent_qualifier = parent_hcl.split(".", 1)[-1]
            ws_resource_name = _resource_name(f"{parent_qualifier}_{name}")
        else:
            ws_resource_name = _resource_name(name)
        return {
            "resource_type": "spacelift_stack",
            "resource_name": ws_resource_name,
            "attributes": ws_attrs,
        }

    return None


@hookimpl
def smk_export_data(vendor_config: dict[str, Any]) -> dict[str, Any] | None:
    """Export data from HCP Terraform or Terraform Enterprise.

    Args:
        vendor_config: Configuration from source.config section.

    Returns:
        Dictionary containing counts of exported entities.
    """
    if vendor_config.get("source_plugin") != "hashicorp":
        return None

    credentials = vendor_config.get("credentials", {})
    product = credentials.get("product", "hcp_terraform")
    address = credentials.get("tfe_hostname", HCP_TF_ADDRESS) if product == "terraform_enterprise" else HCP_TF_ADDRESS

    config = TFEConfig(address=address, token=credentials["token"], max_retries=1)
    client = TFEClient(config)

    data_dir = get_data_dir(subdir="source")

    logger.info("Connecting to %s", address)

    try:
        orgs = list(client.organizations.list())
    except AuthError as e:
        msg = "Authentication failed — check your API token on the Configure page and try again."
        logger.error(msg)
        raise SMKError(msg) from e
    except RateLimited as e:
        retry = int(e.retry_after or 60)
        msg = f"Rate limited by the API — wait {retry}s and retry."
        logger.error(msg)
        raise SMKError(msg) from e
    except ServerError as e:
        msg = f"The API returned a server error ({e}) — check that {address} is reachable."
        logger.error(msg)
        raise SMKError(msg) from e
    except TFEError as e:
        msg = f"API error: {e} — check your configuration and try again."
        logger.error(msg)
        raise SMKError(msg) from e
    except Exception as e:
        msg = f"Could not reach {address}: {e} — check the hostname and your network connection."
        logger.error(msg)
        raise SMKError(msg) from e

    logger.info("Found %d organization(s)", len(orgs))

    projects: list[Any] = []
    workspaces: list[Any] = []
    for org in orgs:
        if org.name is None:
            raise ValueError(f"Organization {org.id} has no name")
        logger.info("Exporting organization: %s", org.name)
        projects.extend(client.projects.list(org.name))
        workspaces.extend(client.workspaces.list(org.name))

    data_dir.mkdir(parents=True, exist_ok=True)
    _write(data_dir / "organizations.json", orgs)
    _write(data_dir / "projects.json", projects)
    _write(data_dir / "workspaces.json", workspaces)

    logger.info(
        "Export complete — %d organization(s), %d project(s), %d workspace(s)",
        len(orgs),
        len(projects),
        len(workspaces),
    )
    return {"organizations": len(orgs), "projects": len(projects), "workspaces": len(workspaces)}
