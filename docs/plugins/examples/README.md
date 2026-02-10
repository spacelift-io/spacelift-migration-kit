# Plugin Examples

This directory contains example plugins demonstrating various patterns and use cases.

## Examples

### 1. Simple Transform (`simple_transform.py`)

**Type**: Single-file plugin

**Purpose**: Basic stack transformation

**Features**:

- Applies naming convention
- Adds standard labels
- Sets default branch based on environment

**Usage**:

```bash
cp simple_transform.py ~/.config/smk/plugins/
```

**No dependencies required.**

### 2. External Enrichment (`external_enrichment/`)

**Type**: Package plugin with dependencies

**Purpose**: Enrich data from external API

**Features**:

- Fetches cost estimates from API
- Adds owner and activity metadata
- Demonstrates error handling

**Usage**:

```bash
cp -r external_enrichment ~/.config/smk/plugins/

# Development mode
uv add requests>=2.32

# Bundled mode: auto-installs
```

**Dependencies**: `requests>=2.32.0`

## Creating Your Own

### Start Simple

Begin with a single-file plugin:

```python
"""My first plugin."""

import pluggy

hookimpl = pluggy.HookimplMarker("smk")


@hookimpl
def smk_transform_stack(stack: dict) -> dict:
    """My transformation."""
    # Your logic here
    return stack
```

Save as `~/.config/smk/plugins/my_plugin.py` and restart SMK.

### Add Complexity

When you need multiple files:

```
my_plugin/
  __init__.py         # Main plugin code
  helpers.py          # Helper functions
  requirements.txt    # Dependencies
  README.md          # Documentation
```

### Learn More

- [Developer Guide](../developer-guide.md) - Complete plugin development guide
- [API Reference](../api-reference.md) - All available hooks
- [User Guide](../user-guide.md) - Installing and using plugins

## Testing Examples

### Test Simple Transform

```bash
# Install
cp simple_transform.py ~/.config/smk/plugins/

# Start SMK
just dev

# Check plugins page
open http://localhost:8000/plugins

# Should see "simple_transform" in loaded plugins
```

### Test External Enrichment

```bash
# Install
cp -r external_enrichment ~/.config/smk/plugins/

# Install dependency (dev mode)
uv add requests>=2.32

# Start SMK
just dev

# Check plugins page
open http://localhost:8000/plugins

# Should see "external_enrichment" in loaded plugins
```

## Contributing Examples

Have a useful plugin pattern? Contribute it:

1. Create plugin following examples structure
1. Add README explaining purpose and usage
1. Test thoroughly
1. Submit PR to SMK repository

Good examples to add:

- Vendor integration plugin
- Configuration validation plugin
- Multi-hook plugin
- Plugin with complex dependencies
