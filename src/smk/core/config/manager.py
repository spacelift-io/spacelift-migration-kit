"""Configuration manager for SMK."""

from pathlib import Path

import yaml

from smk.core.config.models import SMKConfig
from smk.core.config.paths import get_config_file_path, get_data_dir, get_default_config_dir, get_logs_dir
from smk.core.exceptions import ConfigNotInitializedError


class ConfigManager:
    """Manages SMK configuration lifecycle."""

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize ConfigManager.

        Args:
            config_dir: Optional custom config directory. Uses XDG default if None.
        """
        self.config_dir = config_dir or get_default_config_dir()

    @property
    def config_file(self) -> Path:
        """Get the path to the configuration file."""
        return get_config_file_path(self.config_dir)

    @property
    def data_dir(self) -> Path:
        """Get the path to the data directory."""
        return get_data_dir(self.config_dir)

    @property
    def logs_dir(self) -> Path:
        """Get the path to the logs directory."""
        return get_logs_dir(self.config_dir)

    @property
    def state_file(self) -> Path:
        """Get the path to the state file."""
        return self.config_dir / "state.yaml"

    @property
    def is_initialized(self) -> bool:
        """Check if SMK configuration has been initialized."""
        return self.config_file.exists()

    def require_initialized(self) -> None:
        """Raise ConfigNotInitializedError if not initialized."""
        if not self.is_initialized:
            raise ConfigNotInitializedError(str(self.config_dir))

    def init(
        self,
        *,
        force: bool = False,
        source_plugin: str | None = None,
        source_credentials: dict[str, str] | None = None,
        spacelift_endpoint: str | None = None,
        spacelift_key_id: str | None = None,
        spacelift_key_secret: str | None = None,
    ) -> SMKConfig:
        """Initialize SMK configuration.

        Creates the directory structure and configuration file.

        Args:
            force: If True, overwrite existing configuration.
            source_plugin: Source vendor plugin name.
            source_credentials: Credentials for source vendor.
            spacelift_endpoint: Spacelift API endpoint.
            spacelift_key_id: Spacelift API key ID.
            spacelift_key_secret: Spacelift API key secret.

        Returns:
            The created SMKConfig.

        Raises:
            FileExistsError: If config exists and force is False.
        """
        if self.is_initialized and not force:
            raise FileExistsError(f"Configuration already exists at {self.config_file}. Use --force to overwrite.")

        # Create directory structure
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Create data subdirectories
        for subdir in ["generated", "source", "transformed"]:
            get_data_dir(self.config_dir, subdir).mkdir(parents=True, exist_ok=True)

        # Build config
        from smk.core.config.models import SourceVendorConfig, SpaceliftConfig

        config = SMKConfig(
            source=SourceVendorConfig(
                plugin=source_plugin,
                credentials=source_credentials or {},
            ),
            spacelift=SpaceliftConfig(
                api_endpoint=spacelift_endpoint,
                api_key_id=spacelift_key_id,
                api_key_secret=spacelift_key_secret,
            ),
        )

        self.save(config)
        return config

    def load(self) -> SMKConfig:
        """Load configuration from file.

        Returns:
            The loaded SMKConfig.

        Raises:
            ConfigNotInitializedError: If config file doesn't exist.
        """
        self.require_initialized()

        with self.config_file.open() as f:
            data = yaml.safe_load(f) or {}

        return SMKConfig(**data)

    def load_last_step(self) -> str:
        """Load the last visited workflow step from state file.

        Returns:
            The last step ID, or "start" if missing or unreadable.
        """
        try:
            with self.state_file.open() as f:
                data = yaml.safe_load(f) or {}
            return str(data.get("last_step", "start"))
        except Exception:
            return "start"

    def save_last_step(self, step: str) -> None:
        """Save the last visited workflow step to state file.

        Args:
            step: The step ID to save.
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with self.state_file.open("w") as f:
            yaml.dump({"last_step": step}, f, default_flow_style=False)

    def save(self, config: SMKConfig) -> None:
        """Save configuration to file.

        Args:
            config: The configuration to save.
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Convert to dict, excluding None values for cleaner YAML
        data = config.model_dump(exclude_none=True)

        with self.config_file.open("w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=True)


def is_config_initialized(config_dir: Path | None = None) -> bool:
    """Check if SMK configuration has been initialized.

    Args:
        config_dir: Optional custom config directory.

    Returns:
        True if config file exists.
    """
    return ConfigManager(config_dir).is_initialized


def require_config_initialized(config_dir: Path | None = None) -> None:
    """Raise ConfigNotInitializedError if not initialized.

    Args:
        config_dir: Optional custom config directory.

    Raises:
        ConfigNotInitializedError: If config file doesn't exist.
    """
    ConfigManager(config_dir).require_initialized()


def load_config(config_dir: Path | None = None) -> SMKConfig:
    """Load configuration from the default or specified directory.

    Args:
        config_dir: Optional custom config directory.

    Returns:
        The loaded SMKConfig.

    Raises:
        ConfigNotInitializedError: If config file doesn't exist.
    """
    return ConfigManager(config_dir).load()
