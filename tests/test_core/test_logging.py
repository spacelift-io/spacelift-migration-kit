"""Tests for SMK logging setup."""

import json
import logging

import pytest

from smk.core.logging import setup_logging


@pytest.fixture(autouse=True)
def _cleanup_smk_logger():
    """Remove handlers added to the smk logger after each test."""
    yield
    smk_logger = logging.getLogger("smk")
    for handler in smk_logger.handlers[:]:
        handler.close()
        smk_logger.removeHandler(handler)


def test_setup_logging_creates_log_file(tmp_path):
    """setup_logging creates a log file in logs_dir."""
    log_file = setup_logging(tmp_path)
    assert log_file.exists()
    assert log_file.parent == tmp_path
    assert log_file.name.startswith("smk-")
    assert log_file.suffix == ".log"


def test_setup_logging_creates_logs_dir(tmp_path):
    """setup_logging creates logs_dir if it doesn't exist."""
    logs_dir = tmp_path / "nested" / "logs"
    assert not logs_dir.exists()
    log_file = setup_logging(logs_dir)
    assert logs_dir.exists()
    assert log_file.exists()


def test_info_messages_appear_at_info_level(tmp_path):
    """INFO messages are written to the log file at default INFO level."""
    log_file = setup_logging(tmp_path)
    logging.getLogger("smk.test").info("hello world")

    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["level"] == "INFO"
    assert entry["message"] == "hello world"
    assert entry["logger"] == "smk.test"
    assert "time" in entry


def test_debug_messages_suppressed_at_info_level(tmp_path):
    """DEBUG messages are not written when debug=False."""
    log_file = setup_logging(tmp_path, debug=False)
    logging.getLogger("smk.test").debug("hidden")

    assert log_file.read_text().strip() == ""


def test_debug_messages_appear_when_debug_enabled(tmp_path):
    """DEBUG messages are written when debug=True."""
    log_file = setup_logging(tmp_path, debug=True)
    logging.getLogger("smk.test").debug("visible")

    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["level"] == "DEBUG"
    assert entry["message"] == "visible"
