"""External enrichment plugin example.

This plugin demonstrates fetching additional data from an external API
to enrich the exported data with cost estimates and metadata.
"""

import pluggy

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

hookimpl = pluggy.HookimplMarker("smk")

# Configuration
API_URL = "https://api.example.com"


@hookimpl
def smk_post_export(export_data: dict) -> dict:
    """Enrich exported stacks with external API data.

    Args:
        export_data: Raw exported data

    Returns:
        Enriched export data with cost and metadata
    """
    if requests is None:
        print("Warning: requests library not installed, skipping enrichment")  # noqa: T201
        return export_data

    stacks = export_data.get("stacks", [])
    print(f"Enriching {len(stacks)} stacks with external data...")  # noqa: T201

    for stack in stacks:
        try:
            # Fetch additional data
            metadata = fetch_stack_metadata(stack)

            # Add to stack
            stack["cost_estimate"] = metadata.get("monthly_cost")
            stack["owner_team"] = metadata.get("team")
            stack["last_activity"] = metadata.get("last_run")

        except Exception as e:
            print(f"Warning: Failed to enrich stack {stack.get('name')}: {e}")  # noqa: T201
            # Continue with other stacks

    print("Enrichment complete")  # noqa: T201
    return export_data


def fetch_stack_metadata(stack: dict) -> dict:
    """Fetch metadata from external API.

    Args:
        stack: Stack entity

    Returns:
        Metadata dictionary
    """
    if requests is None:
        return {}

    stack_id = stack.get("id")
    if not stack_id:
        return {}

    try:
        response = requests.get(
            f"{API_URL}/stacks/{stack_id}/metadata",
            timeout=5,
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        print(f"API error: {e}")  # noqa: T201
        return {}
