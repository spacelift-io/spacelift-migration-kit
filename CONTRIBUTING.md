# Contributing to Spacelift Migration Kit

Thank you for your interest in contributing to SMK! This guide will help you set up your development environment and
understand our development workflow.

## Prerequisites

- **Python 3.10+** - SMK requires Python 3.10 or higher (CI tests against 3.10, 3.11, 3.12, 3.13, 3.14)
- **uv** - Fast Python package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Git** - Version control
- **just** (optional) - Command runner for development tasks ([installation
  guide](https://github.com/casey/just#installation)) - Not required - use the `justfile` as a reference to run commands
  manually if you prefer

## Getting Started

### Clone the Repository

```bash
git clone https://github.com/spacelift-io/spacelift-migration-kit.git
cd spacelift-migration-kit
```

### Set Up Development Environment

```bash
just setup
source .venv/bin/activate
```

This installs dependencies, activates the virtual environment, and installs pre-commit hooks. Pre-commit hooks
automatically run code quality checks before each commit.

**Note:** If you don't activate the virtual environment, prefix all commands with `uv run` (e.g., `uv run smk --help`,
`uv run pytest`).

### Verify Setup

```bash
just test
```

## Development Workflow

### Running the CLI

```bash
smk --help
```

### Testing

```bash
# Run all tests
just test

# Run tests with coverage report
just test-cov

# Generate HTML coverage report and open in browser
just test-cov-html
```

### Quality Assurance

```bash
# Run all QA checks (lint, format-check, type-check, test-cov)
just qa
```

Run this before committing to catch issues faster. Pre-commit hooks will run these checks automatically on commit.

### Testing Against Multiple Python Versions Locally

The local development environment uses Python 3.14 (configured in `.python-version`), but CI tests against all supported
versions (3.10-3.14). To test against a specific Python version locally:

```bash
# Test with Python 3.12
uv run --python 3.12 pytest

# Run full QA suite with Python 3.11
uv run --python 3.11 pytest --cov --cov-report=term-missing
```

This helps catch version-specific issues before pushing to CI.

### Pre-commit Hooks

Pre-commit hooks automatically run before each commit. See `.pre-commit-config.yaml` for the complete list.

```bash
# Manually run all pre-commit checks
just pre-commit

# Update pre-commit hooks to latest versions
just pre-commit-update
```

## Code Style Guidelines

Most style and quality standards are enforced automatically by pre-commit hooks. The tools will either fix issues
automatically (formatting, line length) or fail with clear error messages (type errors, low coverage, security issues).

### General Principles

- **Alphabetical Order**: Sort items alphabetically when practical (imports, function arguments, dictionary keys, etc.)
  for easier reading and editing
- **Type Hints**: All functions should have type hints (checked automatically)
- **Pure Functions**: Prefer pure functions whenever practical
- **Line Length**: Maximum 120 characters (enforced automatically)

### Quality Standards

- **Test Coverage**: Minimum 80% coverage required (enforced automatically)
- **Type Safety**: All code must pass type checking (checked automatically)
- **Security**: Follow security best practices (checked automatically)

## Development Tools

All tool configurations are defined in `pyproject.toml` and `.pre-commit-config.yaml`.

- **mdformat** - Markdown formatter
- **pyproject-fmt** - Format pyproject.toml
- **Pytest** - Testing framework with coverage reporting
- **Ruff** - Python linter and formatter
- **Ty** - Type checker from Astral

## Making Changes

### Branch Naming

Use descriptive branch names: `feature/add-terraform-support`, `fix/handle-empty-stacks`, `refactor/simplify-plugin-api`

### Commit Messages

- Use imperative mood ("Add feature" not "Added feature")
- Keep first line under 72 characters
- Add details in body if needed

### Pull Requests

1. Create a feature branch
1. Make your changes and add tests
1. Run `just qa` for quick feedback (optional - pre-commit hooks will verify on commit)
1. Commit your changes
1. Push to your fork
1. Open a pull request with clear description and links to related issues

## Architecture Overview

SMK uses a plugin-based architecture:

- **Core Module** (`src/smk/core/`) - Low-level reusable functionality (config, workflow orchestration, plugin
  management via `pluggy`, logging, error handling)
- **Plugins** (`src/smk/plugins/`) - Migration-specific actions (vendor extraction, transformation, IaC updates)

All data is managed as Pydantic models for type safety and validation.

## Getting Help

- Review existing code for patterns and conventions
- Open an issue for questions or clarifications

## License

By contributing, you agree that your contributions will be licensed under [the same license](./LICENSE.txt) as the
project.
