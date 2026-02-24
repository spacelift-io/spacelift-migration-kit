"""Tests for the CLI application."""

from __future__ import annotations

import re

from typer.testing import CliRunner

from smk.core.cli import app

runner = CliRunner()


def strip_ansi(text: str) -> str:
    """
    Remove ANSI escape codes from text.

    KLUDGE: GitHub Actions sets FORCE_COLOR environment variable which causes Rich/Typer
    to output ANSI color codes even when color=False is passed to runner.invoke().
    This breaks string matching in tests because '--version' becomes split as
    '\\x1b[1;36m-\\x1b[0m\\x1b[1;36m-version\\x1b[0m'.
    We strip ANSI codes as a workaround. Ideally, color=False should prevent this.
    """
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def test_app_help():
    """Test that the app shows help."""
    result = runner.invoke(app, ["--help"], color=False)
    output = strip_ansi(result.stdout)
    assert result.exit_code == 0
    assert "Spacelift Migration Kit" in output
    assert "--version" in output
    assert "--help" in output


def test_app_version():
    """Test that the app shows version."""
    result = runner.invoke(app, ["--version"], color=False)
    output = strip_ansi(result.stdout)
    assert result.exit_code == 0
    assert "SMK version" in output


def test_cli_runs_web_server(mocker):
    """Test that CLI runs web server."""
    mock_server = mocker.patch("smk.core.cli.run_server")

    result = runner.invoke(app, [], color=False)

    assert result.exit_code == 0
    mock_server.assert_called_once()


def test_version_callback_package_not_found():
    """version_callback shows 'unknown' when package metadata is missing."""
    from importlib.metadata import PackageNotFoundError
    from unittest.mock import patch

    with patch("smk.core.cli.get_version", side_effect=PackageNotFoundError("smk")):
        result = runner.invoke(app, ["--version"], color=False)

    output = strip_ansi(result.stdout)
    assert "SMK version unknown" in output


def test_main_callback_skips_server_when_subcommand_invoked():
    """main_callback does not call run_server when a subcommand is invoked."""
    from unittest.mock import MagicMock, patch

    from smk.core.cli import main_callback

    ctx = MagicMock()
    ctx.invoked_subcommand = "some-subcommand"

    with patch("smk.core.cli.run_server") as mock_server:
        main_callback(ctx)

    mock_server.assert_not_called()
