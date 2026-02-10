# Plugin System Testing Guide

This guide explains how to test the plugin system in both development and bundled modes.

## Development Mode Testing

Development mode is the default when running SMK from source.

### 1. Start Development Server

```bash
just dev
```

### 2. Check Plugin Status

Navigate to `http://localhost:8000/plugins` in your browser. You should see:

- **Deployment Mode**: "Development Mode"
- **Loaded Plugins**: Empty (no built-in plugins yet)
- **Failed Plugins**: Empty

### 3. Create Test Plugin

Create a test plugin to verify loading works:

```bash
mkdir -p ~/.config/smk/plugins/test_plugin
```

Create `~/.config/smk/plugins/test_plugin/__init__.py`:

```python
import pluggy

hookimpl = pluggy.HookimplMarker("smk")

@hookimpl
def smk_pre_export(batch: dict) -> None:
    """Test plugin hook."""
    print("Test plugin loaded!")
```

### 4. Test Dependency Verification

Create `~/.config/smk/plugins/test_plugin/requirements.txt`:

```
nonexistent-package-xyz
```

Restart the server:

```bash
just dev
```

Navigate to `/plugins` - you should see the plugin in the "Failed Plugins" section with an error message showing:

- "Missing dependencies: nonexistent-package-xyz"
- Helpful command: "Install with: uv add nonexistent-package-xyz"

### 5. Clean Up

```bash
rm -rf ~/.config/smk/plugins/test_plugin
```

## Bundled Mode Testing

Bundled mode is when running the desktop application built with PyInstaller.

### 1. Build Desktop App

**macOS**:

```bash
just build-macos
```

The app will be at `dist/SMK.app`.

**Linux**:

```bash
just build-linux
```

**Windows**:

```bash
just build-windows
```

### 2. Launch Desktop App

**macOS**:

```bash
open dist/SMK.app
```

**Linux**:

```bash
./dist/SMK/SMK
```

**Windows**:

```bash
dist\SMK\SMK.exe
```

### 3. Verify Bundled Mode

Navigate to the Plugins page. You should see:

- **Deployment Mode**: "Bundled Mode"
- Message about automatic dependency installation

### 4. Test Plugin Loading

Create a test plugin (same as development mode):

```bash
mkdir -p ~/.config/smk/plugins/test_plugin
```

Create `~/.config/smk/plugins/test_plugin/__init__.py`:

```python
import pluggy

hookimpl = pluggy.HookimplMarker("smk")

@hookimpl
def smk_pre_export(batch: dict) -> None:
    """Test plugin loaded in bundled mode."""
    print("Bundled plugin works!")
```

Restart the desktop app and check the Plugins page - the plugin should load successfully.

### 5. Test Automatic Dependency Installation

Create `~/.config/smk/plugins/test_plugin/requirements.txt`:

```
requests
```

Restart the desktop app. The plugin system should:

1. Detect the missing dependency
1. Automatically install `requests` to `~/.config/smk/plugin-deps/`
1. Load the plugin successfully

Check the Plugins page - the plugin should appear in "Loaded Plugins".

### 6. Verify Dependency Installation

```bash
ls ~/.config/smk/plugin-deps/
```

You should see the `requests` package and its dependencies.

### 7. Clean Up

```bash
rm -rf ~/.config/smk/plugins/test_plugin
rm -rf ~/.config/smk/plugin-deps/
rm ~/.config/smk/plugin-cache.json
```

## Common Issues

### Issue: Plugin Not Loading

**Symptoms**: Plugin doesn't appear in Loaded or Failed sections.

**Solutions**:

1. Check plugin file structure (needs `__init__.py` or `.py` file)
1. Check plugin is in correct directory (`~/.config/smk/plugins/`)
1. Restart the application

### Issue: Dependency Installation Fails (Bundled Mode)

**Symptoms**: Plugin in Failed section with pip error.

**Solutions**:

1. Check internet connection
1. Verify `sys.executable` points to bundled Python
1. Check permissions on `~/.config/smk/plugin-deps/`

### Issue: Import Error After Dependency Installation

**Symptoms**: Plugin fails with ImportError despite dependency being installed.

**Solutions**:

1. Restart the application (dependencies are only added to sys.path on load)
1. Check dependency was installed to correct location
1. Clear cache: `rm ~/.config/smk/plugin-cache.json`

## Verification Checklist

### Development Mode

- [ ] Plugin manager initializes on startup
- [ ] Plugins page shows "Development Mode"
- [ ] Missing dependencies show helpful error with `uv add` command
- [ ] Valid plugins load successfully
- [ ] Plugin failures don't crash the application

### Bundled Mode

- [ ] Desktop app launches successfully
- [ ] Plugins page shows "Bundled Mode"
- [ ] Built-in plugins from `src/smk/plugins/` load (when they exist)
- [ ] Third-party plugins load from `~/.config/smk/plugins/`
- [ ] Dependencies auto-install to `~/.config/smk/plugin-deps/`
- [ ] Plugin loading works after dependency installation
- [ ] Plugin failures don't crash the application

## Testing on Multiple Platforms

### macOS

- Build with `just build-macos`
- Test .app bundle
- Verify code signing (if applicable)

### Linux

- Build with `just build-linux`
- Test executable
- Verify dependencies are bundled

### Windows

- Build with `just build-windows`
- Test .exe
- Verify Windows-specific paths work

## Advanced Testing

### Test Multiple Plugins

Create several plugins to test:

- Loading order
- Multiple plugins with same hooks
- Plugin dependencies on each other
- Error isolation (one failing plugin doesn't affect others)

### Test Plugin Cache

1. Load a plugin successfully
1. Check `~/.config/smk/plugin-cache.json` exists
1. Restart app - plugin should load faster (from cache)
1. Modify plugin - app should detect change and reload

### Performance Testing

1. Create 10+ simple plugins
1. Measure startup time
1. Verify acceptable performance (\<100ms plugin discovery overhead)
