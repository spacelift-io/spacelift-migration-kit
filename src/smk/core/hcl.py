"""HCL serializer for Spacelift resources."""

from datetime import datetime, timezone
from typing import Any


def _hcl_value(value: Any, indent: int = 2) -> str:
    """Render a single HCL value."""
    if isinstance(value, str):
        if value.startswith("$ref:"):
            # Bare Terraform reference — strip prefix, unquoted
            return value[len("$ref:") :]
        return f'"{value}"'
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, dict):
        return _hcl_block(value, indent)
    if isinstance(value, list):
        items = ", ".join(_hcl_value(v, indent) for v in value)
        return f"[{items}]"
    return f'"{value}"'


def _hcl_block(attrs: dict[str, Any], indent: int = 2) -> str:
    """Render a dict as HCL block body (used for nested blocks)."""
    pad = " " * indent
    lines = ["{"]
    for key, value in sorted(attrs.items()):
        if isinstance(value, dict):
            lines.append(f"{pad}{key} {_hcl_block(value, indent + 2)}")
        else:
            lines.append(f"{pad}{key} = {_hcl_value(value, indent + 2)}")
    lines.append(" " * (indent - 2) + "}")
    return "\n".join(lines)


def entity_to_hcl(spacelift_entity: dict[str, Any]) -> str:
    """Render one resource block.

    Args:
        spacelift_entity: Dict with resource_type, resource_name, attributes.

    Returns:
        HCL resource block string.
    """
    resource_type = spacelift_entity["resource_type"]
    resource_name = spacelift_entity["resource_name"]
    attrs = spacelift_entity.get("attributes", {})

    lines = [f'resource "{resource_type}" "{resource_name}" {{']
    for key, value in sorted(attrs.items()):
        if isinstance(value, dict):
            lines.append(f"  {key} {_hcl_block(value, 4)}")
        else:
            lines.append(f"  {key} = {_hcl_value(value, 4)}")
    lines.append("}")
    return "\n".join(lines)


def batch_to_hcl(batch_id: int, entities: list[dict[str, Any]]) -> str:
    """Generate a full HCL file for a batch.

    Args:
        batch_id: Batch identifier (used in header comment).
        entities: List of spacelift_entity dicts.

    Returns:
        Complete HCL file content as string.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    header = f"# SMK Batch {batch_id} — generated {now}"
    blocks = [entity_to_hcl(e) for e in entities]
    return "\n\n".join([header, *blocks]) + "\n"
