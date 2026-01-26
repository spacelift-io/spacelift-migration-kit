# CLAUDE.md

Guidance for Claude Code when working with this repository.

## Project Overview

The Spacelift Migration Kit (SMK) helps customers migrate their infrastructure management from their current solution to
Spacelift with minimal friction.

## Development

**Package Management**: Always use `uv`. Never manually edit `pyproject.toml`.

- Add: `uv add <package>` or `uv add --dev <package>`
- Remove: `uv remove <package>`
- Sync: `uv sync`

**Key Commands**: See `justfile` for all commands.

- Run CLI: `uv run smk`
- QA checks: `just qa`
- Lint: `just lint` or `just lint-fix`
- Tests: `just test` or `just test-cov`
- Format: `just format`
- Type check: `just type-check`

**After code changes**: Always run `just qa`. Fix all issues before work is complete.

**Multi-version testing**: CI tests against Python 3.10-3.14. Local dev uses 3.14. Test against specific versions with `uv run --python 3.12 pytest`.

## Architecture

**Core Module** (`src/smk/core/`): Low-level reusable functionality (config, workflow orchestration, plugin management
via `pluggy`, logging, error handling).

**Plugins** (`src/smk/plugins/`): Migration-specific actions (vendor extraction, transformation, IaC updates). All
extensibility through plugins. No core modifications needed.

**Plugin System**: Uses `pluggy`. Plugins register via hook specifications. Everything achievable through plugins.

**Data Management**: Collections of Pydantic models for type safety and validation.

1. Export all data upfront
1. Process in batches
1. Validate at every step
1. Never fail silently

**CLI**: Pattern is `smk <subject> <action>` (e.g., `smk stack export`). Built with `typer`. Optional `textual` TUI maps
to CLI commands.

## Design Principles

1. **AI-Friendly**: Organize codebase for easy AI navigation and extension.
1. **Integrity**: Validate data throughout workflow. Be paranoid.
1. **UX**: Proactive guidance, meaningful errors, suggest next steps.
1. **Extensibility**: Everything via plugins. Core only for low-level reusables.
1. **Speed**: Parallelize, batch, pre-load.
1. **Robustness**: Comprehensive test coverage.
1. **Pure Functions**: Use whenever practical.

## Code Style

- **Alphabetical Order**: Sort alphabetically (functions, arguments, imports, config keys, just recipes).
- **Documentation**: Link to source of truth (pyproject.toml, .pre-commit-config.yaml, justfile) instead of duplicating.
- **KLUDGE Comments**: Use `KLUDGE:` comments for non-ideal solutions where no better approach exists. Explain the problem, why this solution was chosen, and what conditions would allow it to be removed. Include links to relevant issues or documentation when helpful. This helps future maintainers understand workarounds and when to revisit them.

## Tech Stack

- Python 3.10+ (CI tested: 3.10, 3.11, 3.12, 3.13, 3.14)
- `pluggy` (plugins)
- `pydantic` (models)
- `pydantic-settings` (config)
- `pytest` (tests)
- `textual` (TUI)
- `typer` (CLI)
- `uv` (packages)
