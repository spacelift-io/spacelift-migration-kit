"""HashiCorp source plugin for SMK.

Supports both HCP Terraform (formerly Terraform Cloud) and self-hosted
Terraform Enterprise. The distinction is controlled by the `product` field.
"""

import pluggy

hookimpl = pluggy.HookimplMarker("smk")

HCP_TF_HOSTNAME = "app.terraform.io"

PRODUCT_OPTIONS = [
    {"label": "HCP Terraform (Terraform Cloud)", "value": "hcp_terraform"},
    {"label": "Terraform Enterprise (self-hosted)", "value": "terraform_enterprise"},
]


@hookimpl
def smk_get_source_info() -> dict:
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
def smk_export_data(vendor_config: dict) -> dict:
    """Export data from HCP Terraform or Terraform Enterprise.

    Args:
        vendor_config: Configuration from source.config section.

    Returns:
        Dictionary containing exported entities.
    """
    credentials = vendor_config.get("credentials", {})
    product = credentials.get("product", "hcp_terraform")

    _hostname = credentials.get("tfe_hostname", "") if product == "terraform_enterprise" else HCP_TF_HOSTNAME

    # Stub: real implementation would use _hostname + credentials["token"]
    return {"policies": [], "spaces": [], "stacks": []}
