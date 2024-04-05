"""Pytest configuration."""

import pytest
from click.testing import CliRunner


@pytest.fixture(scope="module")
def runner() -> CliRunner:
    """Fixture for invoking CLI commands in tests."""
    return CliRunner()
