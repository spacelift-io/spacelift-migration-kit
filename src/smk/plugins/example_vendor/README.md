# Example Vendor Plugin

Reference implementation of a built-in vendor plugin for SMK.

## Purpose

This plugin demonstrates the structure and patterns for creating vendor integration plugins. It uses mock data instead of real API calls, making it useful for:

- **Development**: Testing the plugin system without external dependencies
- **Documentation**: Reference implementation showing best practices
- **Testing**: Providing realistic test data for the migration workflow

## Features

### Data Export

Implements `smk_export_data` hook to return mock infrastructure data:

- 2 example stacks (production and staging)
- 1 example space (engineering)
- 3 example policies (approval, cost, auto-approve)

### Post-Apply Guidance

Implements `smk_get_post_apply_guidance` hook to provide manual migration steps:

- Verification procedures
- Webhook updates
- Stack archival process
- Documentation updates
- Cleanup timeline

### Automated Actions

Implements `smk_post_apply_actions` hook to demonstrate post-migration automation:

- Labeling migrated stacks
- Locking source stacks
- Sending notifications
- Adding migration metadata

## Configuration

To use this plugin, configure it as the source vendor:

```yaml
# ~/.config/smk/config.yaml
source:
  plugin: example_vendor
  config:
    # Plugin-specific configuration would go here
    api_url: https://api.example.com
    api_token: ${EXAMPLE_VENDOR_TOKEN}
```

## Real Vendor Plugins

When creating a real vendor plugin:

1. **Copy this structure** as a starting point
1. **Replace mock data** with actual API calls
1. **Add authentication** handling
1. **Implement error handling** for API failures
1. **Add retry logic** for transient errors
1. **Include rate limiting** if needed
1. **Add dependencies** to requirements.txt if using HTTP clients
1. **Write tests** mocking the vendor API

## Data Structure

The export data structure returned by `smk_export_data` should include:

```python
{
    "stacks": [
        {
            "id": str,              # Unique identifier
            "name": str,            # Stack name
            "description": str,     # Description
            "environment": str,     # Environment (prod, staging, dev)
            "repository": str,      # VCS repository URL
            "branch": str,          # VCS branch
            "terraform_version": str,
            "labels": list[str],
            "variables": dict,      # Environment variables
            "policies": list[str],  # Policy IDs
        }
    ],
    "spaces": [...],    # Workspace groupings
    "policies": [...],  # Policy definitions
}
```

## Integration

This plugin is automatically discovered and loaded by the plugin manager when:

1. Listed in `config.yaml` under `source.plugin`
1. Located in `src/smk/plugins/` directory (built-in)

No manual installation required - it's bundled with SMK.

## See Also

- [Developer Guide](../../../docs/plugins/developer-guide.md) - Complete plugin development guide
- [API Reference](../../../docs/plugins/api-reference.md) - All available hooks
- [User Guide](../../../docs/plugins/user-guide.md) - Using plugins
