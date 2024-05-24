import json
import logging
import subprocess
from importlib.metadata import version
from pathlib import Path
from shutil import which
from typing import Optional

import gitinfo
from benedict import benedict
from packaging.version import Version as PyPIVersion
from semver import Version as SemVerVersion


def pypi_version_to_semver(version: str) -> str:
    pypi_version = PyPIVersion(version)

    if pypi_version.dev is not None:
        info = gitinfo.get_git_info()
        build = info["commit"][0:7] if info is not None else "unknown"
        pre = "dev"
    elif pypi_version.pre is not None:
        build = None
        pre_mapping = {"a": "alpha", "b": "beta", "pre": "rc"}
        pre = f"{pre_mapping[pypi_version.pre[0]]}{pypi_version.pre[1]}"
    else:
        pre = None
        build = None

    return str(SemVerVersion(*pypi_version.release, build=build, prerelease=pre))


__version__ = pypi_version_to_semver(version("spacemk"))


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


def save_normalized_data(data: dict, path: Optional[str | Path] = None) -> None:
    if not path:
        path = Path(get_tmp_folder(), "data.json")
    elif isinstance(path, str):
        path = Path(path)
    elif not isinstance(path, Path):
        raise ValueError("The path argument must be a string or a Path object.")

    with path.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2, sort_keys=True)
