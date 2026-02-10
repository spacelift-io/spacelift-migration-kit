# Plugin User Guide

This guide explains how to install and use plugins with the Spacelift Migration Kit (SMK).

## What Are Plugins?

Plugins extend SMK's functionality by adding:

- **Vendor integrations**: Support for additional migration sources (Terraform Cloud, GitHub Actions, etc.)
- **Custom transformations**: Modify how entities are migrated
- **Workflow enhancements**: Add capabilities to any migration stage

## Plugin Directory

Plugins are installed in:

```
~/.config/smk/plugins/
```

This directory is created automatically when you first run SMK.

## Viewing Installed Plugins

### Web Interface

1. Start SMK: `just dev` (or launch desktop app)
1. Navigate to the Plugins page
1. See loaded and failed plugins with status

### Plugin Status

**Loaded Plugins** (green):

- Successfully loaded and active
- Ready to use in migrations

**Failed Plugins** (red):

- Failed to load
- Shows error message and resolution steps

## Installing Plugins

### Method 1: Download and Extract

```bash
# Create plugins directory if it doesn't exist
mkdir -p ~/.config/smk/plugins

# Download plugin
curl -L https://example.com/plugin.zip -o plugin.zip

# Extract to plugins directory
unzip plugin.zip -d ~/.config/smk/plugins/

# Restart SMK
```

### Method 2: Git Clone

```bash
# Clone plugin repository
cd ~/.config/smk/plugins/
git clone https://github.com/example/smk-my-plugin.git

# Restart SMK
```

### Method 3: Manual Copy

```bash
# Copy plugin files
cp -r /path/to/plugin ~/.config/smk/plugins/my_plugin

# Restart SMK
```

## Plugin Dependencies

Plugins may require additional Python packages.

### Development Mode (Running from Source)

When running SMK from source with `just dev`:

1. Plugin fails with error: `"Missing dependencies: boto3>=1.35"`
1. Install manually:
   ```bash
   uv add boto3>=1.35
   # or
   pip install boto3>=1.35
   ```
1. Restart SMK: `just dev`
1. Plugin loads successfully

### Bundled Mode (Desktop Application)

When using the SMK desktop app (.app or .exe):

1. Plugin dependencies **automatically install**
1. See progress indicator in web UI
1. Dependencies install to `~/.config/smk/plugin-deps/`
1. Plugin loads after installation completes

**Note**: First load may take a minute while dependencies install.

## Configuring Plugins

### Enable/Disable Plugins

Edit `~/.config/smk/config.yaml`:

```yaml
plugins:
  enabled:
    - terraform-cloud
    - custom-transform
```

Only listed plugins will load. Remove from list to disable.

### Plugin-Specific Configuration

Some plugins use configuration from `config.yaml`:

```yaml
source:
  plugin: terraform-cloud
  organization: my-org
  api_token: ${TFC_TOKEN}
```

Check plugin documentation for configuration options.

## Uninstalling Plugins

```bash
# Remove plugin directory
rm -rf ~/.config/smk/plugins/my_plugin

# Remove plugin dependencies (bundled mode)
rm -rf ~/.config/smk/plugin-deps/

# Clear plugin cache
rm ~/.config/smk/plugin-cache.json

# Restart SMK
```

## Troubleshooting

### Plugin Not Appearing

**Check location**:

```bash
ls -la ~/.config/smk/plugins/
```

Ensure plugin is in correct directory.

**Check structure**:

```
my_plugin/
  __init__.py     # Required for directory plugins
```

Or:

```
my_plugin.py      # Single-file plugin
```

**Restart SMK**: Changes require restart to take effect.

### Plugin Failed to Load

Navigate to `/plugins` page to see error message.

**Common issues**:

1. **Missing dependencies** (Development mode):

   ```
   Error: Missing dependencies: requests>=2.32
   Solution: Run: uv add requests>=2.32
   ```

1. **Import error**:

   ```
   Error: ModuleNotFoundError: No module named 'requests'
   Solution: Install dependency and restart
   ```

1. **Syntax error**:

   ```
   Error: SyntaxError: invalid syntax
   Solution: Check plugin code for errors
   ```

### Dependencies Not Installing (Bundled Mode)

**Check internet connection**: Auto-install requires network access.

**Check permissions**:

```bash
ls -ld ~/.config/smk/plugin-deps/
```

Ensure directory is writable.

**Manual cleanup**:

```bash
# Remove failed installation
rm -rf ~/.config/smk/plugin-deps/
rm ~/.config/smk/plugin-cache.json

# Restart app to retry
```

### Plugin Loads But Doesn't Work

1. **Check plugin is enabled** in `config.yaml`:

   ```yaml
   plugins:
     enabled:
       - my-plugin
   ```

1. **Check logs** for errors during execution

1. **Verify plugin configuration** matches documentation

1. **Contact plugin author** with error details

## Using Plugins

### Built-in Plugins

SMK includes plugins for common migration sources. These are pre-installed and documented in the main SMK documentation.

### Vendor Plugins

To use a vendor plugin:

1. Install the plugin (see Installation above)
1. Configure in `config.yaml`:
   ```yaml
   source:
     plugin: plugin-name
     # Plugin-specific settings
   ```
1. Restart SMK
1. Run migration as normal

The plugin handles vendor-specific operations automatically.

### Transformation Plugins

Transformation plugins modify data during migration:

1. Install plugin
1. Add to enabled list:
   ```yaml
   plugins:
     enabled:
       - custom-transform
   ```
1. Configure if needed
1. Run migration

Transformations apply automatically during workflow.

## Finding Plugins

### Official Plugins

Check SMK documentation for officially supported plugins.

### Community Plugins

- GitHub: Search for `smk-plugin`
- SMK Community: Plugin sharing forum (future)

### Request Support

If you need support for a specific vendor:

1. Check if plugin exists
1. Request in SMK GitHub discussions
1. Hire developer to create custom plugin
1. Develop plugin yourself (see [Developer Guide](developer-guide.md))

## Security Considerations

### Trust

**Plugins execute code on your machine**. Only install plugins from trusted sources:

- Official SMK plugins
- Verified community plugins
- Plugins you wrote/reviewed yourself

### Review Code

Before installing:

1. Check plugin source code
1. Verify no malicious behavior
1. Check dependencies are legitimate

### Sandboxing

Plugins run with same permissions as SMK:

- Can read/write files
- Can make network requests
- Can execute commands

**Do not run SMK with elevated privileges** unless necessary.

### Credentials

Plugins may need credentials (API tokens, etc.):

- Use environment variables
- Never commit credentials to config files
- Rotate credentials regularly

## Best Practices

1. **One purpose per plugin**: Easier to manage and troubleshoot
1. **Keep plugins updated**: Check for updates regularly
1. **Test before production**: Verify plugin works with test data
1. **Document configuration**: Save plugin settings in version control (without secrets)
1. **Monitor plugin page**: Check for failed plugins after updates
1. **Backup before changes**: Save config before installing new plugins

## Getting Help

### Plugin Issues

1. Check plugin documentation
1. Review error message on `/plugins` page
1. Search plugin repository issues
1. Contact plugin author

### SMK Issues

1. Check [SMK documentation](../../README.md)
1. Review [troubleshooting guide](../architecture/plugin-testing.md)
1. Open issue on [SMK GitHub](https://github.com/spacelift-io/smk)

## Example Workflows

### Installing Terraform Cloud Plugin

```bash
# 1. Install plugin
git clone https://github.com/spacelift-io/smk-terraform-cloud \
  ~/.config/smk/plugins/terraform-cloud

# 2. Configure
cat >> ~/.config/smk/config.yaml <<EOF
source:
  plugin: terraform-cloud
  organization: my-org
  api_token: \${TFC_TOKEN}
EOF

# 3. Set token
export TFC_TOKEN=your-token-here

# 4. Restart and verify
just dev
open http://localhost:8000/plugins
```

### Installing Custom Transformation

```bash
# 1. Copy plugin
cp custom_transform.py ~/.config/smk/plugins/

# 2. Enable in config
cat >> ~/.config/smk/config.yaml <<EOF
plugins:
  enabled:
    - custom_transform
EOF

# 3. Restart
just dev
```

### Using Multiple Plugins

```yaml
# config.yaml
plugins:
  enabled:
    - terraform-cloud # Vendor integration
    - custom-labels # Add labels to all entities
    - naming-convention # Enforce naming standards

source:
  plugin: terraform-cloud
  organization: my-org
```

Plugins execute in order during appropriate workflow stages.

## Next Steps

- [Developer Guide](developer-guide.md) - Create your own plugins
- [API Reference](api-reference.md) - Available hooks and interfaces
- [Testing Guide](../architecture/plugin-testing.md) - Test plugins thoroughly
- [Example Plugins](examples/) - Learn from examples
