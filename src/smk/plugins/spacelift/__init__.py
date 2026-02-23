"""Spacelift source plugin for SMK.

Supports account-to-account migration from one Spacelift account to another.
"""

import pluggy

hookimpl = pluggy.HookimplMarker("smk")


@hookimpl
def smk_get_source_info() -> dict:
    """Return source plugin metadata for the configure UI."""
    return {
        "plugin_id": "spacelift",
        "display_name": "Spacelift",
        "description": "Migrate from one Spacelift account to another.",
        "fields": [
            {
                "key": "account_url",
                "label": "Account URL",
                "type": "url",
                "required": True,
                "placeholder": "https://example.app.spacelift.io",
                "help_text": "URL of your source Spacelift account.",
            },
            {
                "key": "api_key_id",
                "label": "API Key ID",
                "type": "text",
                "required": True,
                "placeholder": "",
                "help_text": "ID of the API key used for authentication.",
            },
            {
                "key": "api_key_secret",
                "label": "API Key Secret",
                "type": "password",
                "required": True,
                "placeholder": "",
                "help_text": "Secret of the API key used for authentication.",
            },
        ],
    }


@hookimpl
def smk_export_data(vendor_config: dict) -> dict | None:
    """Export data from source Spacelift account.

    Args:
        vendor_config: Configuration from source.config section.

    Returns:
        Dictionary containing exported entities.
    """
    if vendor_config.get("source_plugin") != "spacelift":
        return None
    # Stub: real implementation would use vendor_config["credentials"]
    return {"policies": [], "spaces": [], "stacks": []}
