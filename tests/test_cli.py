"""Tests for the CLI application."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from typer.testing import CliRunner

from smk.core.cli import app

if TYPE_CHECKING:
    from pathlib import Path

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


def test_app_no_args(mocker):
    """Test that the app launches TUI when no args provided."""
    mock_tui = mocker.patch("smk.core.tui.TUIApp", autospec=True)
    mock_instance = mock_tui.return_value

    result = runner.invoke(app, [], color=False)

    assert result.exit_code == 0
    mock_tui.assert_called_once()
    mock_instance.run.assert_called_once()


def test_app_invalid_command():
    """Test that invalid commands show an error."""
    result = runner.invoke(app, ["invalid"], color=False)
    assert result.exit_code != 0
    # Error message might be in stderr
    output = strip_ansi(result.stdout + result.stderr)
    assert "No such command" in output or "Error" in output


class TestConfigInit:
    """Tests for smk config init command."""

    def test_config_init_help(self):
        """Test that config init shows help."""
        result = runner.invoke(app, ["config", "init", "--help"], color=False)
        output = strip_ansi(result.stdout)
        assert result.exit_code == 0
        assert "Initialize SMK configuration" in output
        assert "--config-dir" in output
        assert "--force" in output
        assert "--source" in output

    def test_config_init_creates_config(self, tmp_path: Path):
        """Test that config init creates configuration."""
        result = runner.invoke(
            app,
            [
                "config",
                "init",
                "--config-dir",
                str(tmp_path),
                "--source",
                "terraform-cloud",
                "--spacelift-endpoint",
                "https://example.app.spacelift.io",
                "--spacelift-key-id",
                "key123",
                "--spacelift-key-secret",
                "secret456",
            ],
            color=False,
        )
        output = strip_ansi(result.stdout)
        assert result.exit_code == 0
        assert "Configuration initialized" in output
        assert (tmp_path / "config.yaml").exists()

    def test_config_init_interactive(self, tmp_path: Path):
        """Test that config init prompts for missing values."""
        result = runner.invoke(
            app,
            ["config", "init", "--config-dir", str(tmp_path)],
            input="terraform-cloud\nhttps://example.app.spacelift.io\nkey123\nsecret456\n",
            color=False,
        )
        output = strip_ansi(result.stdout)
        assert result.exit_code == 0
        assert "Configuration initialized" in output

    def test_config_init_fails_if_exists(self, tmp_path: Path):
        """Test that config init fails if config exists."""
        # First init
        runner.invoke(
            app,
            [
                "config",
                "init",
                "--config-dir",
                str(tmp_path),
                "--source",
                "test",
                "--spacelift-endpoint",
                "",
                "--spacelift-key-id",
                "",
                "--spacelift-key-secret",
                "",
            ],
            color=False,
        )

        # Second init should fail
        result = runner.invoke(
            app,
            [
                "config",
                "init",
                "--config-dir",
                str(tmp_path),
                "--source",
                "test2",
                "--spacelift-endpoint",
                "",
                "--spacelift-key-id",
                "",
                "--spacelift-key-secret",
                "",
            ],
            color=False,
        )
        assert result.exit_code == 1
        output = strip_ansi(result.stderr)
        assert "already exists" in output
        assert "--force" in output

    def test_config_init_force_overwrites(self, tmp_path: Path):
        """Test that config init --force overwrites existing config."""
        # First init
        runner.invoke(
            app,
            [
                "config",
                "init",
                "--config-dir",
                str(tmp_path),
                "--source",
                "old-plugin",
                "--spacelift-endpoint",
                "",
                "--spacelift-key-id",
                "",
                "--spacelift-key-secret",
                "",
            ],
            color=False,
        )

        # Force init
        result = runner.invoke(
            app,
            [
                "config",
                "init",
                "--config-dir",
                str(tmp_path),
                "--force",
                "--source",
                "new-plugin",
                "--spacelift-endpoint",
                "",
                "--spacelift-key-id",
                "",
                "--spacelift-key-secret",
                "",
            ],
            color=False,
        )
        assert result.exit_code == 0


class TestConfigShow:
    """Tests for smk config show command."""

    def test_config_show_help(self):
        """Test that config show shows help."""
        result = runner.invoke(app, ["config", "show", "--help"], color=False)
        output = strip_ansi(result.stdout)
        assert result.exit_code == 0
        assert "Show current configuration" in output

    def test_config_show_not_initialized(self, tmp_path: Path):
        """Test that config show fails if not initialized."""
        result = runner.invoke(
            app,
            ["config", "show", "--config-dir", str(tmp_path)],
            color=False,
        )
        assert result.exit_code == 1
        output = strip_ansi(result.stderr)
        assert "not initialized" in output

    def test_config_show_displays_config(self, tmp_path: Path):
        """Test that config show displays configuration."""
        # First init
        runner.invoke(
            app,
            [
                "config",
                "init",
                "--config-dir",
                str(tmp_path),
                "--source",
                "terraform-cloud",
                "--spacelift-endpoint",
                "https://example.app.spacelift.io",
                "--spacelift-key-id",
                "key123",
                "--spacelift-key-secret",
                "secret456",
            ],
            color=False,
        )

        # Show config
        result = runner.invoke(
            app,
            ["config", "show", "--config-dir", str(tmp_path)],
            color=False,
        )
        output = strip_ansi(result.stdout)
        assert result.exit_code == 0
        assert "terraform-cloud" in output
        assert "https://example.app.spacelift.io" in output
        assert "key123" in output
        assert "***" in output  # Secret should be masked
