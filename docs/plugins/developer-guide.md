# Plugin Developer Guide

This guide explains how to create plugins for the Spacelift Migration Kit (SMK).

## Overview

SMK uses [pluggy](https://pluggy.readthedocs.io/) for its plugin system. Plugins can hook into various stages of the migration workflow to customize behavior, add vendor support, or extend functionality.

## Plugin Architecture

### Core Concepts

- **Hooks**: Specific points in the workflow where plugins can execute code
- **Hook Implementations**: Functions in your plugin that implement hooks
- **Plugin Manager**: Loads and manages plugins
- **Deployment Modes**: Development (manual deps) vs Bundled (auto deps)

### Plugin Types

**Built-in Plugins**: Bundled with SMK in `src/smk/plugins/`

- Loaded automatically on startup
- No installation required
- Example: Terraform Cloud integration

**Third-party Plugins**: User-created plugins in `~/.config/smk/plugins/`

- Installed by users
- Can be shared via git/packages
- Example: Custom transformation logic

## Creating Your First Plugin

### Minimal Plugin (Single File)

Create `~/.config/smk/plugins/hello_plugin.py`:

```python
"""A simple hello world plugin."""

import pluggy

hookimpl = pluggy.HookimplMarker("smk")


@hookimpl
def smk_pre_export(batch: dict) -> None:
    """Called before export stage begins."""
    print(f"Hello from plugin! Processing batch: {batch}")
```

That's it! SMK will automatically discover and load this plugin.

### Package Plugin (Directory)

For more complex plugins, use a directory structure:

```
~/.config/smk/plugins/my_plugin/
├── __init__.py          # Plugin entry point
├── plugin.yaml          # Metadata (optional)
├── requirements.txt     # Dependencies (optional)
├── transforms.py        # Helper modules
└── README.md           # Documentation
```

**`__init__.py`**:

```python
"""My custom SMK plugin."""

import pluggy

from .transforms import custom_transform

hookimpl = pluggy.HookimplMarker("smk")


@hookimpl
def smk_transform_stack(stack: dict) -> dict:
    """Transform stack with custom logic."""
    return custom_transform(stack)
```

**`transforms.py`**:

```python
"""Transformation utilities."""


def custom_transform(stack: dict) -> dict:
    """Apply custom transformations."""
    # Your logic here
    stack["custom_field"] = "value"
    return stack
```

### Plugin Metadata (Optional)

Create `plugin.yaml` to provide metadata:

```yaml
name: my-awesome-plugin
version: 1.0.0
description: Custom transformations for my use case
author: you@example.com
requires:
  - requests>=2.32
  - boto3>=1.35
```

This is optional but helpful for documentation and tooling.

## Hook Specifications

### Available Hooks

See [API Reference](api-reference.md) for complete hook documentation.

**Export Stage**:

- `smk_pre_export(batch)` - Before export begins
- `smk_export_data(vendor_config)` - Vendor-specific export
- `smk_post_export(export_data)` - After export completes

**Transform Stage**:

- `smk_pre_transform(export_data)` - Before transformation
- `smk_transform_stack(stack)` - Transform individual stack
- `smk_transform_space(space)` - Transform individual space
- `smk_post_transform(transformed_data)` - After transformation

**Generate Stage**:

- `smk_pre_generate(transformed_data)` - Before HCL generation
- `smk_generate_hcl(entities)` - Generate HCL code
- `smk_post_generate(hcl_code)` - After HCL generation

**Apply Stage**:

- `smk_pre_apply(batch)` - Before apply
- `smk_post_apply(apply_result)` - After apply completes

**Post-Apply Actions**:

- `smk_post_apply_actions(entities)` - Vendor-specific actions
- `smk_get_post_apply_guidance()` - Manual guidance text

### Hook Implementation

```python
import pluggy

hookimpl = pluggy.HookimplMarker("smk")


@hookimpl
def smk_transform_stack(stack: dict) -> dict:
    """Transform a stack entity.

    Args:
        stack: Stack data from source vendor

    Returns:
        Transformed stack mapped to Spacelift model
    """
    # Read source data
    source_name = stack.get("name")
    source_branch = stack.get("branch", "main")

    # Transform to Spacelift format
    spacelift_stack = {
        "name": f"migrated-{source_name}",
        "branch": source_branch,
        "repository": stack.get("repo_url"),
        # Add more fields...
    }

    return spacelift_stack
```

## Dependencies

### Declaring Dependencies

Create `requirements.txt` in your plugin directory:

```
requests>=2.32.0
boto3>=1.35.0
pyyaml>=6.0.0
```

### Deployment Mode Behavior

**Development Mode** (running from source):

- Dependencies NOT auto-installed
- SMK shows helpful error: `"Run: uv add boto3>=1.35.0"`
- You manually install with `uv add` or `pip install`

**Bundled Mode** (desktop .app/.exe):

- Dependencies auto-installed to `~/.config/smk/plugin-deps/`
- User sees progress indicator in web UI
- Automatic on first plugin load

### Best Practices

1. **Pin minimum versions**: `boto3>=1.35` not `boto3`
1. **Use standard packages**: Prefer packages with binary wheels
1. **Document dependencies**: Explain why each is needed
1. **Test both modes**: Verify plugin works in dev and bundled

## Testing Your Plugin

### Manual Testing

1. **Development mode**:

   ```bash
   # Place plugin in directory
   mkdir -p ~/.config/smk/plugins/my_plugin
   cp my_plugin.py ~/.config/smk/plugins/my_plugin/__init__.py

   # Start SMK
   just dev

   # Check /plugins page
   open http://localhost:8000/plugins
   ```

1. **Bundled mode**:

   ```bash
   # Build app
   just build-macos

   # Launch
   open dist/SMK.app

   # Check plugins page
   ```

See [Testing Guide](../architecture/plugin-testing.md) for detailed testing procedures.

### Unit Testing

```python
"""Test my plugin."""

import pytest
from my_plugin import custom_transform


def test_custom_transform():
    """Test transformation logic."""
    input_stack = {
        "name": "old-stack",
        "branch": "develop",
    }

    result = custom_transform(input_stack)

    assert result["name"] == "migrated-old-stack"
    assert result["branch"] == "develop"
```

## Common Patterns

### Conditional Logic

```python
@hookimpl
def smk_transform_stack(stack: dict) -> dict:
    """Apply conditional transformations."""
    # Only modify production stacks
    if stack.get("environment") == "production":
        stack["protection"] = True

    # Add labels based on source
    if stack.get("team") == "platform":
        stack["labels"] = ["team:platform", "priority:high"]

    return stack
```

### External API Calls

```python
import requests

@hookimpl
def smk_post_export(export_data: dict) -> dict:
    """Enrich data with external API."""
    for stack in export_data.get("stacks", []):
        # Fetch additional metadata
        response = requests.get(
            f"https://api.example.com/stacks/{stack['id']}"
        )
        if response.ok:
            stack["metadata"] = response.json()

    return export_data
```

### Configuration Files

```python
import yaml
from pathlib import Path


def load_plugin_config():
    """Load plugin configuration."""
    config_file = Path.home() / ".config" / "smk" / "my_plugin.yaml"

    if config_file.exists():
        with config_file.open() as f:
            return yaml.safe_load(f)

    return {}


@hookimpl
def smk_transform_stack(stack: dict) -> dict:
    """Use configuration in transformations."""
    config = load_plugin_config()
    naming_pattern = config.get("naming_pattern", "{name}")

    stack["name"] = naming_pattern.format(name=stack["name"])
    return stack
```

### Error Handling

```python
@hookimpl
def smk_transform_stack(stack: dict) -> dict:
    """Transform with error handling."""
    try:
        # Your transformation logic
        result = perform_complex_transform(stack)
        return result
    except KeyError as e:
        # Log error with context
        print(f"Missing required field in stack {stack.get('id')}: {e}")
        # Return original or raise
        return stack
    except Exception as e:
        print(f"Unexpected error transforming stack: {e}")
        raise  # Re-raise to mark plugin as failed
```

## Vendor Integration Plugins

### Structure

Vendor plugins provide complete integration with a source platform:

```python
"""Terraform Cloud plugin."""

import pluggy

hookimpl = pluggy.HookimplMarker("smk")


@hookimpl
def smk_export_data(vendor_config: dict) -> dict:
    """Export from Terraform Cloud."""
    # Use vendor_config to authenticate and fetch data
    org = vendor_config["organization"]
    api_token = vendor_config["api_token"]

    # Fetch workspaces, variables, etc.
    data = fetch_from_terraform_cloud(org, api_token)

    return {
        "stacks": data["workspaces"],
        "variables": data["variables"],
    }


@hookimpl
def smk_post_apply_actions(entities: list[dict]) -> list[dict]:
    """Perform post-migration actions."""
    for entity in entities:
        # Migrate state files, update source code, etc.
        migrate_terraform_state(entity)

    return entities


@hookimpl
def smk_get_post_apply_guidance() -> str:
    """Provide manual guidance."""
    return """
    ## Manual Steps Required

    1. Update Terraform Cloud workspace settings
    2. Archive old workspaces
    3. Update team permissions
    """
```

### Registration

Vendor plugins should be configured in `config.yaml`:

```yaml
source:
  plugin: terraform-cloud
  organization: my-org
  api_token: ${TFC_TOKEN}
```

## Distribution

### Sharing Your Plugin

**Option 1: Git Repository**

```bash
# Users clone and symlink
git clone https://github.com/you/smk-my-plugin
ln -s $(pwd)/smk-my-plugin ~/.config/smk/plugins/my_plugin
```

**Option 2: Direct Download**

```bash
# Users download and extract
curl -L https://github.com/you/smk-plugin/archive/main.zip -o plugin.zip
unzip plugin.zip -d ~/.config/smk/plugins/
```

**Option 3: Python Package** (future)

```bash
# Future: Install via pip/uv
uv add smk-my-plugin
```

### Documentation

Include in your plugin repository:

- **README.md**: Installation and usage
- **CHANGELOG.md**: Version history
- **LICENSE**: Open source license
- **examples/**: Example configurations

## Best Practices

1. **Single Responsibility**: One plugin = one purpose
1. **Minimal Dependencies**: Fewer deps = easier maintenance
1. **Error Messages**: Clear, actionable error messages
1. **Documentation**: Explain what, why, and how
1. **Type Hints**: Use type annotations
1. **Testing**: Test your plugin thoroughly
1. **Versioning**: Use semantic versioning
1. **Compatibility**: Test with multiple SMK versions

## Debugging

### Enable Debug Output

Set environment variable:

```bash
SMK_DEBUG=1 just dev
```

### Check Plugin Status

Navigate to `http://localhost:8000/plugins` to see:

- Loaded plugins
- Failed plugins with error messages
- Deployment mode
- Dependency status

### Common Issues

**Plugin not loading**: Check file structure, needs `__init__.py`

**Import errors**: Check dependencies are installed

**Hook not called**: Verify hook name matches specification

## Examples

See [Example Plugins](examples/) directory for:

- Simple transformation plugin
- Vendor integration plugin
- Multi-hook plugin
- Plugin with dependencies

## Further Reading

- [API Reference](api-reference.md) - Complete hook documentation
- [User Guide](user-guide.md) - Installing and using plugins
- [Testing Guide](../architecture/plugin-testing.md) - Testing procedures
- [Data Workflow](../architecture/data-workflow.md) - Understanding workflow stages
- [pluggy Documentation](https://pluggy.readthedocs.io/) - Plugin framework
