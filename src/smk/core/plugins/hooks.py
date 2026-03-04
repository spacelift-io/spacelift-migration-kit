"""Hook specifications for SMK plugin system.

Defines the plugin interface aligned with SMK data workflow stages.
See docs/architecture/data-workflow.md for full workflow specification.
"""

import pluggy

hookspec = pluggy.HookspecMarker("smk")


# Source Plugin Registration Hooks
@hookspec
def smk_get_source_info() -> dict | None:
    """Return source plugin metadata for the configure UI.

    Source plugins implement this to advertise their display name, description,
    and configuration fields. Non-source plugins return None or omit this hook.

    Returns:
        Dict matching SourcePluginInfo schema, or None.
    """
    raise NotImplementedError


@hookspec
def smk_get_entity_types(source_plugin: str) -> list[dict] | None:
    """Return entity types exported by this plugin.

    Args:
        source_plugin: Active source plugin id. Return None if not your plugin.

    Returns:
        List of dicts matching EntityType schema, or None.
    """
    raise NotImplementedError


# Audit Stage Hooks
@hookspec
def smk_audit_entity_type(
    entity_type: str,
    entities: list[dict],
    source_plugin: str,
) -> list[dict] | None:
    """Audit entities of a given type, return issues.

    Args:
        entity_type: Entity type id being audited.
        entities: Raw entities loaded from source export files.
        source_plugin: Active source plugin id. Return None if not your plugin.

    Returns:
        List of dicts matching AuditIssue schema, or None.
    """
    raise NotImplementedError


# Export Stage Hooks
@hookspec
def smk_export_data(vendor_config: dict) -> dict:
    """Export data from source vendor.

    Vendor-specific plugin exports data from the source platform.

    Args:
        vendor_config: Configuration for the source vendor.

    Returns:
        Exported data dictionary containing source platform entities.
    """
    raise NotImplementedError


@hookspec
def smk_post_export(export_data: dict) -> dict:
    """Modify exported data after export stage.

    Called after export completes. Can modify or enrich exported data.

    Args:
        export_data: Raw data exported from source vendor.

    Returns:
        Modified export data.
    """
    raise NotImplementedError


@hookspec
def smk_pre_export(batch: dict) -> None:
    """Pre-export hook called before export begins.

    Args:
        batch: Batch configuration and metadata.
    """
    raise NotImplementedError


# Migration Stage Hooks
@hookspec
def smk_transform_entity(
    entity_type: str,
    entity: dict,
    source_plugin: str,
) -> dict | None:
    """Transform a source entity into a Spacelift resource dict.

    The entity dict may contain "_smk_parent_hcl_resource_name" injected by
    the manager if a migrated/selected parent exists.

    Args:
        entity_type: Entity type id (e.g. 'workspaces').
        entity: Raw source entity dict (from export JSON).
        source_plugin: Active source plugin id. Return None if not your plugin.

    Returns:
        {
          "resource_type": str,    # e.g. "spacelift_stack"
          "resource_name": str,    # Terraform identifier, e.g. "ws_prod_api"
          "attributes": dict,      # values prefixed "$ref:" are TF references
        }
        Returns None if not this plugin's entity type.
    """
    raise NotImplementedError


# Apply Stage Hooks
@hookspec
def smk_post_apply(apply_result: dict) -> None:
    """Post-apply hook called after apply completes.

    Args:
        apply_result: Results from admin stack apply.
    """
    raise NotImplementedError


@hookspec
def smk_pre_apply(batch: dict) -> None:
    """Pre-apply hook called before apply stage.

    Args:
        batch: Batch configuration and metadata.
    """
    raise NotImplementedError


# Post-Apply Actions (Vendor-Specific)
@hookspec
def smk_get_post_apply_guidance() -> str:
    """Get manual guidance for post-apply actions.

    Vendor plugin provides instructions for manual actions user must perform.

    Returns:
        Markdown-formatted guidance text.
    """
    raise NotImplementedError


@hookspec
def smk_post_apply_actions(entities: list[dict]) -> list[dict]:
    """Perform vendor-specific post-apply actions.

    Vendor plugin performs automated post-apply actions like state migration,
    module version updates, or source repository updates.

    Args:
        entities: List of migrated entities.

    Returns:
        List of entities with post-apply actions completed.
    """
    raise NotImplementedError
