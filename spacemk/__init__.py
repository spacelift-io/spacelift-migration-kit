import subprocess
from pathlib import Path
from shutil import which


def ensure_folder_exists(path: Path | str) -> None:
    if isinstance(path, str):
        path = Path(path).resolve()

    if not path.exists():
        path.mkdir(parents=True)


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
