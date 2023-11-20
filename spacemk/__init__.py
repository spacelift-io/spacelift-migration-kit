import json
import logging
import subprocess
from pathlib import Path
from shutil import which

from benedict import benedict


def ensure_folder_exists(path: Path | str) -> None:
    if isinstance(path, str):
        path = Path(path).resolve()

    if not path.exists():
        logging.debug(f"Creating the '{path}' folder")
        path.mkdir(parents=True)
    else:
        logging.debug(f"The '{path}' folder already exists. Skipping creation.")


def get_tmp_folder() -> Path:
    current_file = Path(__file__).parent.resolve()
    tmp_folder = Path(current_file, "../tmp").resolve()

    ensure_folder_exists(tmp_folder)

    return tmp_folder


def get_tmp_subfolder(path: str) -> Path:
    subfolder = Path(get_tmp_folder(), path).resolve()

    ensure_folder_exists(subfolder)

    return subfolder


def is_command_available(command: str | list[str], execute: bool = False) -> bool:
    if execute:
        try:
            return subprocess.run(command, capture_output=True, check=False).returncode == 0
        except FileNotFoundError:
            return False

    return which(command) is not None


def load_normalized_data() -> dict:
    path = Path(get_tmp_folder(), "data.json")
    with path.open("r", encoding="utf-8") as fp:
        return benedict(json.load(fp))


def save_normalized_data(data: dict) -> None:
    path = Path(get_tmp_folder(), "data.json")
    with path.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2, sort_keys=True)
