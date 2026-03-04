"""XDG path resolution for SMK configuration."""

from pathlib import Path

from xdg_base_dirs import xdg_config_home


def get_default_config_dir() -> Path:
    """Get the default SMK configuration directory.

    Returns the XDG config home directory with 'smk' subdirectory.
    Typically ~/.config/smk on Linux/macOS.
    """
    return xdg_config_home() / "smk"


def get_config_file_path(config_dir: Path | None = None) -> Path:
    """Get the path to the SMK configuration file.

    Args:
        config_dir: Optional custom config directory. Uses default if None.

    Returns:
        Path to config.yaml file.
    """
    if config_dir is None:
        config_dir = get_default_config_dir()
    return config_dir / "config.yaml"


def get_data_dir(config_dir: Path | None = None, subdir: str | None = None) -> Path:
    """Get the path to the SMK data directory.

    Args:
        config_dir: Optional custom config directory. Uses default if None.
        subdir: Optional subdirectory within data (e.g., 'source', 'transformed', 'generated').

    Returns:
        Path to data directory or subdirectory.
    """
    if config_dir is None:
        config_dir = get_default_config_dir()
    data_dir = config_dir / "data"
    if subdir:
        return data_dir / subdir
    return data_dir


def get_logs_dir(config_dir: Path | None = None) -> Path:
    """Get the path to the SMK logs directory.

    Args:
        config_dir: Optional custom config directory. Uses default if None.

    Returns:
        Path to logs directory.
    """
    if config_dir is None:
        config_dir = get_default_config_dir()
    return config_dir / "logs"


def get_plugin_cache_file(config_dir: Path | None = None) -> Path:
    """Get the path to the plugin cache file.

    Args:
        config_dir: Optional custom config directory. Uses default if None.

    Returns:
        Path to plugin-cache.json file.
    """
    if config_dir is None:
        config_dir = get_default_config_dir()
    return config_dir / "plugin-cache.json"


def get_plugin_deps_dir(config_dir: Path | None = None) -> Path:
    """Get the path to the plugin dependencies directory.

    Args:
        config_dir: Optional custom config directory. Uses default if None.

    Returns:
        Path to plugin-deps directory.
    """
    if config_dir is None:
        config_dir = get_default_config_dir()
    return config_dir / "plugin-deps"


def get_db_path(config_dir: Path | None = None) -> Path:
    """Get the path to the SMK SQLite database.

    Args:
        config_dir: Optional custom config directory. Uses default if None.

    Returns:
        Path to smk.db file.
    """
    if config_dir is None:
        config_dir = get_default_config_dir()
    return config_dir / "smk.db"


def get_output_dir(config_dir: Path | None = None) -> Path:
    """Get the path to the SMK HCL output directory.

    Args:
        config_dir: Optional custom config directory. Uses default if None.

    Returns:
        Path to output directory.
    """
    if config_dir is None:
        config_dir = get_default_config_dir()
    return config_dir / "output"


def get_plugins_dir(config_dir: Path | None = None) -> Path:
    """Get the path to the third-party plugins directory.

    Args:
        config_dir: Optional custom config directory. Uses default if None.

    Returns:
        Path to plugins directory.
    """
    if config_dir is None:
        config_dir = get_default_config_dir()
    return config_dir / "plugins"
