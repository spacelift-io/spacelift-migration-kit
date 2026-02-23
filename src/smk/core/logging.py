"""Logging configuration for SMK."""

import json
import logging
from datetime import datetime
from pathlib import Path


class _JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            }
        )


def setup_logging(logs_dir: Path, *, debug: bool = False) -> Path:
    """Configure SMK file logging for this session.

    Creates a new timestamped log file for each app startup. No auto-deletion
    — users manage log files via the Logs page.

    Args:
        logs_dir: Directory to write log files. Created if absent.
        debug: If True, sets level to DEBUG; otherwise INFO.

    Returns:
        Path to the log file for this session (for SSE streaming).
    """
    logs_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%dT%H%M%S")
    log_file = logs_dir / f"smk-{timestamp}.log"

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(_JSONFormatter())

    root_logger = logging.getLogger("smk")
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    root_logger.addHandler(file_handler)

    return log_file
