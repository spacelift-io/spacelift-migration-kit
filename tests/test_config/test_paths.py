"""Tests for config path resolution."""

from pathlib import Path

import pytest

from smk.core.config.paths import get_config_file_path, get_data_dir, get_default_config_dir, get_logs_dir


def test_get_default_config_dir():
    """Default config dir should be under XDG config home."""
    config_dir = get_default_config_dir()
    assert config_dir.name == "smk"
    assert "config" in str(config_dir).lower() or ".config" in str(config_dir)


def test_get_config_file_path_default():
    """Config file path should be config.yaml in default dir."""
    config_file = get_config_file_path()
    assert config_file.name == "config.yaml"
    assert config_file.parent == get_default_config_dir()


def test_get_config_file_path_custom():
    """Config file path should respect custom dir."""
    custom_dir = Path("/custom/path")
    config_file = get_config_file_path(custom_dir)
    assert config_file == Path("/custom/path/config.yaml")


def test_get_data_dir_default():
    """Data dir should be under config dir."""
    data_dir = get_data_dir()
    assert data_dir.name == "data"
    assert data_dir.parent == get_default_config_dir()


def test_get_data_dir_custom():
    """Data dir should respect custom config dir."""
    custom_dir = Path("/custom/path")
    data_dir = get_data_dir(custom_dir)
    assert data_dir == Path("/custom/path/data")


@pytest.mark.parametrize("subdir", ["generated", "source", "transformed"])
def test_get_data_dir_with_subdir(subdir: str):
    """Data dir should support subdirectories."""
    custom_dir = Path("/custom/path")
    data_subdir = get_data_dir(custom_dir, subdir)
    assert data_subdir == Path(f"/custom/path/data/{subdir}")


def test_get_logs_dir_default():
    """Logs dir should be under config dir."""
    logs_dir = get_logs_dir()
    assert logs_dir.name == "logs"
    assert logs_dir.parent == get_default_config_dir()


def test_get_logs_dir_custom():
    """Logs dir should respect custom config dir."""
    custom_dir = Path("/custom/path")
    logs_dir = get_logs_dir(custom_dir)
    assert logs_dir == Path("/custom/path/logs")
