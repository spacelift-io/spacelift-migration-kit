"""Web server configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class WebConfig(BaseSettings):
    """Configuration for the SMK web server."""

    model_config = SettingsConfigDict(env_prefix="SMK_WEB_")

    debug: bool = False
    host: str = "127.0.0.1"
    open_browser: bool = True
    port: int = 8000
