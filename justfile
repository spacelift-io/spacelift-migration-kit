set quiet:= true

_list:
    just --list

# Build desktop app for Linux
build-linux: web-css
    uv run pyinstaller smk.spec --clean --noconfirm
    echo "Built: dist/Spacelift-Migration-Kit"

# Build macOS DMG installer (requires create-dmg)
build-dmg: build-macos
    #!/usr/bin/env bash
    set -euo pipefail
    if ! command -v create-dmg &> /dev/null; then
        echo "Error: create-dmg not found. Install with: brew install create-dmg"
        exit 1
    fi
    rm -f dist/"Spacelift Migration Kit.dmg"
    create-dmg \
        --volname "Spacelift Migration Kit" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --app-drop-link 450 185 \
        "dist/Spacelift Migration Kit.dmg" \
        "dist/Spacelift Migration Kit.app"
    echo "Built: dist/Spacelift Migration Kit.dmg"

# Build application icons from SVG source
build-icons:
    bash scripts/build-icons.sh

# Build desktop app for macOS
build-macos: web-css
    uv run pyinstaller smk.spec --clean --noconfirm
    echo "Built: dist/Spacelift Migration Kit.app"

# Build desktop app for Windows
build-windows: web-css
    uv run pyinstaller smk.spec --clean --noconfirm
    echo "Built: dist/Spacelift-Migration-Kit.exe"

# Clean all build and test artifacts
clean:
    rm -rf build dist *.spec.bak        # PyInstaller artifacts
    rm -rf .pytest_cache                # Pytest cache
    rm -rf htmlcov .coverage            # Coverage reports
    find . -type d -name __pycache__ -exec rm -rf {} +  # Python cache
    find . -type f -name "*.pyc" -delete                # Compiled Python

# Upgrade all dependencies to their latest acceptable versions
deps-upgrade:
    uv lock --upgrade
    uv sync

# Run web development server with auto-reload (primary dev mode)
dev:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "Starting CSS watcher and dev server..."
    # Start CSS watcher in background
    (cd src/smk/core/web/tailwind && uv run tailwindcss -i input.css -o ../static/css/styles.css --watch) &
    CSS_PID=$!
    # Trap EXIT to kill CSS watcher when server stops
    trap "kill $CSS_PID 2>/dev/null || true" EXIT
    # Start dev server (blocks until Ctrl+C)
    SMK_WEB_DEBUG=true SMK_WEB_RELOAD=true uv run smk

# Run desktop app in development (no auto-reload, use dev for rapid iteration)
desktop-dev: web-css
    SMK_WEB_DEBUG=true uv run python -m smk.core.desktop

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
    uv sync --extra desktop  # Install dependencies including desktop
    uv run pre-commit install  # Install pre-commit hooks
    echo "Run 'source .venv/bin/activate' to activate the Python virtual environment"

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

# Build Tailwind CSS
web-css:
    cd src/smk/core/web/tailwind && uv run tailwindcss -i input.css -o ../static/css/styles.css --minify
