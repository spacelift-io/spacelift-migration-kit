# Plugin API Reference

Complete reference for SMK plugin hooks and interfaces.

## Overview

SMK plugins use the [pluggy](https://pluggy.readthedocs.io/) framework. Plugins implement hooks at specific points in the migration workflow.

## Hook Marker

All hook implementations must use the `@hookimpl` decorator:

```python
import pluggy

hookimpl = pluggy.HookimplMarker("smk")


@hookimpl
def smk_pre_export(batch: dict) -> None:
    """Your implementation."""
    pass
```

## Export Stage Hooks

### `smk_pre_export`

Called before export stage begins.

**Signature**:

```python
@hookimpl
def smk_pre_export(batch: dict) -> None:
    """Pre-export hook."""
```

**Parameters**:

- `batch` (dict): Batch configuration and metadata
  - `batch_id` (str): Unique batch identifier
  - `entities` (list): Entity IDs to export
  - `config` (dict): User configuration

**Returns**: None

**Use Cases**:

- Log export start
- Validate configuration
- Initialize resources

**Example**:

```python
@hookimpl
def smk_pre_export(batch: dict) -> None:
    """Log export start."""
    print(f"Starting export for batch: {batch['batch_id']}")
    print(f"Exporting {len(batch['entities'])} entities")
```

### `smk_export_data`

Export data from source vendor. **Vendor plugins only**.

**Signature**:

```python
@hookimpl
def smk_export_data(vendor_config: dict) -> dict:
    """Export from vendor."""
```

**Parameters**:

- `vendor_config` (dict): Vendor-specific configuration
  - Keys depend on vendor (API tokens, org names, etc.)

**Returns**:

- `dict`: Exported data
  - `stacks` (list): Stack/workflow entities
  - `spaces` (list): Organization/project entities
  - `variables` (list): Variables/secrets
  - Additional vendor-specific data

**Use Cases**:

- Fetch data from vendor API
- Read vendor configuration files
- Export vendor state

**Example**:

```python
@hookimpl
def smk_export_data(vendor_config: dict) -> dict:
    """Export from Terraform Cloud."""
    import requests

    org = vendor_config["organization"]
    token = vendor_config["api_token"]

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/vnd.api+json",
    }

    # Fetch workspaces
    resp = requests.get(
        f"https://app.terraform.io/api/v2/organizations/{org}/workspaces",
        headers=headers,
    )
    workspaces = resp.json()["data"]

    return {
        "stacks": workspaces,
        "spaces": [{"name": org, "id": org}],
    }
```

### `smk_post_export`

Modify exported data after export completes.

**Signature**:

```python
@hookimpl
def smk_post_export(export_data: dict) -> dict:
    """Post-process export data."""
```

**Parameters**:

- `export_data` (dict): Raw exported data
  - `stacks` (list): Exported stacks
  - `spaces` (list): Exported spaces
  - Vendor-specific fields

**Returns**:

- `dict`: Modified export data (same structure)

**Use Cases**:

- Enrich data with external sources
- Filter out unwanted entities
- Add metadata

**Example**:

```python
@hookimpl
def smk_post_export(export_data: dict) -> dict:
    """Filter out archived stacks."""
    active_stacks = [
        stack for stack in export_data.get("stacks", [])
        if not stack.get("archived", False)
    ]

    export_data["stacks"] = active_stacks
    return export_data
```

## Transform Stage Hooks

### `smk_pre_transform`

Called before transformation stage begins.

**Signature**:

```python
@hookimpl
def smk_pre_transform(export_data: dict) -> None:
    """Pre-transform hook."""
```

**Parameters**:

- `export_data` (dict): Exported data from export stage

**Returns**: None

**Use Cases**:

- Validate export data structure
- Log transformation start
- Cache reference data

### `smk_transform_stack`

Transform individual stack entity.

**Signature**:

```python
@hookimpl
def smk_transform_stack(stack: dict) -> dict:
    """Transform stack entity."""
```

**Parameters**:

- `stack` (dict): Stack entity from source vendor
  - Structure varies by vendor
  - Contains all stack/workflow configuration

**Returns**:

- `dict`: Transformed stack (Spacelift format)
  - `name` (str): Stack name
  - `repository` (str): Git repository URL
  - `branch` (str): Git branch
  - `space_id` (str): Parent space ID
  - Additional Spacelift stack fields

**Use Cases**:

- Map vendor stack to Spacelift stack
- Apply naming conventions
- Set default values
- Add labels/tags

**Example**:

```python
@hookimpl
def smk_transform_stack(stack: dict) -> dict:
    """Transform with naming convention."""
    # Apply naming convention
    original_name = stack["name"]
    stack["name"] = f"prod-{original_name}"

    # Add labels
    stack["labels"] = [
        "migrated",
        f"source:{original_name}",
    ]

    # Set defaults
    stack.setdefault("branch", "main")
    stack.setdefault("terraform_version", "1.9.0")

    return stack
```

### `smk_transform_space`

Transform individual space entity.

**Signature**:

```python
@hookimpl
def smk_transform_space(space: dict) -> dict:
    """Transform space entity."""
```

**Parameters**:

- `space` (dict): Space/organization entity from source

**Returns**:

- `dict`: Transformed space (Spacelift format)
  - `name` (str): Space name
  - `parent_space_id` (str | None): Parent space
  - `description` (str): Space description
  - Additional Spacelift space fields

**Use Cases**:

- Map vendor organizations to Spacelift spaces
- Create space hierarchy
- Set space permissions

**Example**:

```python
@hookimpl
def smk_transform_space(space: dict) -> dict:
    """Create space with defaults."""
    return {
        "name": space["name"],
        "description": f"Migrated from {space.get('source', 'vendor')}",
        "parent_space_id": None,  # Root space
        "labels": ["migrated"],
    }
```

### `smk_post_transform`

Modify transformed data after transformation completes.

**Signature**:

```python
@hookimpl
def smk_post_transform(transformed_data: dict) -> dict:
    """Post-process transformed data."""
```

**Parameters**:

- `transformed_data` (dict): Transformed Spacelift entities
  - `stacks` (list): Transformed stacks
  - `spaces` (list): Transformed spaces

**Returns**:

- `dict`: Modified transformed data

**Use Cases**:

- Cross-entity validation
- Relationship setup
- Global modifications

**Example**:

```python
@hookimpl
def smk_post_transform(transformed_data: dict) -> dict:
    """Ensure all stacks have a space."""
    default_space_id = "default"

    for stack in transformed_data.get("stacks", []):
        if not stack.get("space_id"):
            stack["space_id"] = default_space_id

    return transformed_data
```

## Generate Stage Hooks

### `smk_pre_generate`

Called before HCL generation begins.

**Signature**:

```python
@hookimpl
def smk_pre_generate(transformed_data: dict) -> None:
    """Pre-generate hook."""
```

**Parameters**:

- `transformed_data` (dict): Transformed Spacelift entities

**Returns**: None

**Use Cases**:

- Validate transformed data
- Log generation start

### `smk_generate_hcl`

Generate HCL code for entities. **Advanced use only**.

**Signature**:

```python
@hookimpl
def smk_generate_hcl(entities: list[dict]) -> str:
    """Generate HCL code."""
```

**Parameters**:

- `entities` (list[dict]): List of transformed Spacelift entities

**Returns**:

- `str`: Generated HCL code

**Use Cases**:

- Custom HCL generation logic
- Alternative template system

**Example**:

```python
@hookimpl
def smk_generate_hcl(entities: list[dict]) -> str:
    """Generate HCL with custom formatting."""
    hcl_blocks = []

    for entity in entities:
        if entity["type"] == "stack":
            hcl = f'''
resource "spacelift_stack" "{entity['id']}" {{
  name       = "{entity['name']}"
  repository = "{entity['repository']}"
  branch     = "{entity['branch']}"
}}
'''
            hcl_blocks.append(hcl)

    return "\n".join(hcl_blocks)
```

### `smk_post_generate`

Modify generated HCL after generation completes.

**Signature**:

```python
@hookimpl
def smk_post_generate(hcl_code: str) -> str:
    """Post-process HCL code."""
```

**Parameters**:

- `hcl_code` (str): Generated HCL code

**Returns**:

- `str`: Modified HCL code

**Use Cases**:

- Add comments
- Format code
- Insert custom blocks

**Example**:

```python
@hookimpl
def smk_post_generate(hcl_code: str) -> str:
    """Add header comment."""
    header = """
# Generated by SMK
# Date: {date}
# DO NOT EDIT MANUALLY
"""
    from datetime import datetime
    return header.format(date=datetime.now()) + hcl_code
```

## Apply Stage Hooks

### `smk_pre_apply`

Called before apply stage begins.

**Signature**:

```python
@hookimpl
def smk_pre_apply(batch: dict) -> None:
    """Pre-apply hook."""
```

**Parameters**:

- `batch` (dict): Batch being applied

**Returns**: None

**Use Cases**:

- Validate prerequisites
- Backup existing state
- Log apply start

### `smk_post_apply`

Called after apply completes.

**Signature**:

```python
@hookimpl
def smk_post_apply(apply_result: dict) -> None:
    """Post-apply hook."""
```

**Parameters**:

- `apply_result` (dict): Results from apply
  - `success` (bool): Apply succeeded
  - `created` (list): Created resources
  - `errors` (list): Any errors

**Returns**: None

**Use Cases**:

- Log apply results
- Trigger notifications
- Update external systems

## Post-Apply Actions

### `smk_post_apply_actions`

Perform vendor-specific post-apply actions. **Vendor plugins only**.

**Signature**:

```python
@hookimpl
def smk_post_apply_actions(entities: list[dict]) -> list[dict]:
    """Vendor-specific actions."""
```

**Parameters**:

- `entities` (list[dict]): Migrated entities

**Returns**:

- `list[dict]`: Updated entities

**Use Cases**:

- Migrate Terraform state
- Update source code
- Archive old resources

**Example**:

```python
@hookimpl
def smk_post_apply_actions(entities: list[dict]) -> list[dict]:
    """Migrate Terraform state files."""
    for entity in entities:
        if entity["type"] == "stack":
            # Migrate state from old workspace to Spacelift
            migrate_state(
                from_workspace=entity["source_id"],
                to_stack=entity["spacelift_id"],
            )
            entity["state_migrated"] = True

    return entities
```

### `smk_get_post_apply_guidance`

Provide manual guidance text. **Vendor plugins only**.

**Signature**:

```python
@hookimpl
def smk_get_post_apply_guidance() -> str:
    """Manual guidance for user."""
```

**Parameters**: None

**Returns**:

- `str`: Markdown-formatted guidance text

**Use Cases**:

- Document manual steps
- Provide verification checklist
- Link to resources

**Example**:

````python
@hookimpl
def smk_get_post_apply_guidance() -> str:
    """Provide post-migration guidance."""
    return """
## Post-Migration Steps

### 1. Verify Stacks

- Check all stacks exist in Spacelift
- Verify repository connections work
- Test a plan on each stack

### 2. Archive Old Workspaces

```bash
# Archive Terraform Cloud workspaces
terraform-cloud archive-workspace <name>
````

### 3. Update Team Access

- Review Spacelift space permissions
- Grant access to relevant teams
- Remove old vendor access

### 4. Update Documentation

- Update runbooks with new Spacelift links
- Document the migration process
  """

````

## Data Structures

### Batch

```python
{
    "batch_id": "batch-001",
    "entities": ["stack-1", "stack-2"],
    "config": {
        "source": {...},
        "spacelift": {...},
    },
}
````

### Stack Entity (Source)

Structure varies by vendor. Common fields:

```python
{
    "id": "ws-12345",
    "name": "my-stack",
    "repository": "github.com/org/repo",
    "branch": "main",
    "terraform_version": "1.9.0",
    # Vendor-specific fields
}
```

### Stack Entity (Spacelift)

```python
{
    "name": "my-stack",
    "repository": "github.com/org/repo",
    "branch": "main",
    "space_id": "space-id",
    "terraform_version": "1.9.0",
    "labels": ["migrated"],
    # Additional Spacelift fields
}
```

### Export Data

```python
{
    "stacks": [...],  # List of stack entities
    "spaces": [...],  # List of space entities
    "variables": [...],  # Variables/secrets
    # Vendor-specific data
}
```

## Hook Execution Order

### Single Plugin

Hooks execute in workflow order:

1. `smk_pre_export`
1. `smk_export_data`
1. `smk_post_export`
1. `smk_pre_transform`
1. `smk_transform_stack` (for each stack)
1. `smk_transform_space` (for each space)
1. `smk_post_transform`
1. `smk_pre_generate`
1. `smk_generate_hcl`
1. `smk_post_generate`
1. `smk_pre_apply`
1. `smk_post_apply`
1. `smk_post_apply_actions`
1. `smk_get_post_apply_guidance`

### Multiple Plugins

When multiple plugins implement the same hook:

- Plugins execute in registration order
- Each plugin receives the output of the previous
- Last plugin's return value is used

## Error Handling

### Plugin Errors

If a plugin hook raises an exception:

1. Error is logged with stack trace
1. Plugin marked as failed
1. SMK continues with other plugins
1. User sees error on `/plugins` page

### Best Practices

```python
@hookimpl
def smk_transform_stack(stack: dict) -> dict:
    """Transform with error handling."""
    try:
        # Your logic
        return transform_logic(stack)
    except KeyError as e:
        # Log and return original
        print(f"Missing field: {e}")
        return stack
    except Exception as e:
        # Log and re-raise for critical errors
        print(f"Critical error: {e}")
        raise
```

## Type Hints

Use type hints for better IDE support:

```python
import pluggy
from typing import Any

hookimpl = pluggy.HookimplMarker("smk")


@hookimpl
def smk_transform_stack(stack: dict[str, Any]) -> dict[str, Any]:
    """Type-hinted implementation."""
    name: str = stack["name"]
    # ...
    return stack
```

## Further Reading

- [Developer Guide](developer-guide.md) - Creating plugins
- [User Guide](user-guide.md) - Installing plugins
- [Data Workflow](../architecture/data-workflow.md) - Workflow stages
- [pluggy Documentation](https://pluggy.readthedocs.io/) - Plugin framework
