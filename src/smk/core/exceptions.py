"""SMK exceptions."""


class SMKError(Exception):
    """Base exception for all SMK errors."""


class ConfigNotInitializedError(SMKError):
    """Raised when config is required but not initialized."""

    def __init__(self, config_dir: str | None = None) -> None:
        if config_dir:
            message = f"SMK is not initialized. Run 'smk config init' to initialize. Config dir: {config_dir}"
        else:
            message = "SMK is not initialized. Run 'smk config init' to initialize."
        super().__init__(message)
