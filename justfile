set quiet:= true

_list:
    just --list

# Format code and config files
format:
    uv run mdformat .  # Format Markdown files
    uv run pyproject-fmt pyproject.toml  # Format pyproject.toml
    uv run ruff format  # Format Python files

# Check formatting without applying changes
format-check:
    uv run mdformat --check .  # Check Markdown formatting
    uv run pyproject-fmt --check pyproject.toml  # Check pyproject.toml formatting
    uv run ruff format --check  # Check Python formatting

# Check code for issues
lint:
    uv run ruff check

# Fix auto-fixable issues
lint-fix:
    uv run ruff check --fix

# Run all pre-commit hooks
pre-commit:
    uv run pre-commit run --all-files

# Update pre-commit hooks
pre-commit-update:
    uv run pre-commit autoupdate --freeze

# Run all quality assurance checks
qa: lint format-check type-check test-cov

# Set local dev environment up
setup:
    uv sync  # Install dependencies
    uv run pre-commit install  # Install pre-commit hooks
    echo "Run `source .venv/bin/activate` to activate the Python virtual environment"

# Run automated tests
test:
    uv run pytest

# Run tests with coverage
test-cov:
    uv run pytest --cov --cov-report=term-missing

# Generate HTML coverage report
test-cov-html:
    uv run pytest --cov --cov-report=html  # Generate HTML coverage report
    echo "Opening coverage report in browser..."
    open htmlcov/index.html  # Open report in browser

# Check types
type-check:
    uv run ty check
