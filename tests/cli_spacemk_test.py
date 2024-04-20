"""Tests for the root CLI command."""

from click.testing import CliRunner

from spacemk import cli


def test_spacemk_succeeds(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(cli.spacemk)
    assert result.exit_code == 0
