"""HashiCorp source plugin for SMK.

Supports both HCP Terraform (formerly Terraform Cloud) and self-hosted
Terraform Enterprise. The distinction is controlled by the `product` field.
"""

from __future__ import annotations

import logging
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
