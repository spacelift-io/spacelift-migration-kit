import subprocess
from shutil import which


def is_command_available(command: str, execute: bool = False) -> bool:
    if execute:
        return subprocess.run(command, capture_output=True, check=False).returncode == 0

    return which(command) is not None
