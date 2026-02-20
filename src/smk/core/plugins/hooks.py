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


# Transform Stage Hooks
@hookspec
def smk_post_transform(transformed_data: dict) -> dict:
    """Modify transformed data after transformation stage.

    Called after transformation completes. Can modify transformed entities.

    Args:
        transformed_data: Transformed Spacelift entities.

    Returns:
        Modified transformed data.
    """
    raise NotImplementedError


@hookspec
def smk_pre_transform(export_data: dict) -> None:
    """Pre-transform hook called before transformation begins.

    Args:
        export_data: Exported data from source vendor.
    """
    raise NotImplementedError


@hookspec
def smk_transform_space(space: dict) -> dict:
    """Transform individual space entity.

    Args:
        space: Space entity from source platform.

    Returns:
        Transformed space entity mapped to Spacelift model.
    """
    raise NotImplementedError


@hookspec
def smk_transform_stack(stack: dict) -> dict:
    """Transform individual stack entity.

    Args:
        stack: Stack entity from source platform.

    Returns:
        Transformed stack entity mapped to Spacelift model.
    """
    raise NotImplementedError


# Generate Stage Hooks
@hookspec
def smk_generate_hcl(entities: list[dict]) -> str:
    """Generate HCL code for entities.

    Args:
        entities: List of transformed Spacelift entities.

    Returns:
        Generated HCL code as string.
    """
    raise NotImplementedError


@hookspec
def smk_post_generate(hcl_code: str) -> str:
    """Modify generated HCL after generation stage.

    Called after HCL generation completes. Can modify generated code.

    Args:
        hcl_code: Generated HCL code.

    Returns:
        Modified HCL code.
    """
    raise NotImplementedError


@hookspec
def smk_pre_generate(transformed_data: dict) -> None:
    """Pre-generate hook called before HCL generation begins.

    Args:
        transformed_data: Transformed Spacelift entities.
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
