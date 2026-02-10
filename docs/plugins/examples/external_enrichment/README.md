# External Enrichment Plugin

This plugin demonstrates enriching exported data with information from an external API.

## Features

- Fetches additional metadata from external service
- Adds cost tracking information
- Uses requests library for HTTP calls

## Installation

```bash
# Copy plugin to SMK plugins directory
cp -r external_enrichment ~/.config/smk/plugins/

# Install dependencies (development mode)
uv add requests>=2.32

# Or bundled mode will auto-install
```

## Configuration

No configuration required. Modify `API_URL` in `__init__.py` to point to your API.

## Usage

Enable in `~/.config/smk/config.yaml`:

```yaml
plugins:
  enabled:
    - external_enrichment
```

The plugin will automatically enrich exported stacks with:

- Cost estimates
- Owner information
- Last activity timestamp
