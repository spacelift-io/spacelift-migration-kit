"""Pydantic models for SMK configuration."""

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PluginConfig(BaseModel):
    """Configuration for enabled plugins."""

    enabled: list[str] = Field(default_factory=list)


class SourceVendorConfig(BaseModel):
    """Configuration for the source vendor (migration source)."""

    plugin: str | None = None
    credentials: dict[str, str] = Field(default_factory=dict)


class SpaceliftConfig(BaseModel):
    """Configuration for Spacelift API connection."""

    api_endpoint: str | None = None
    api_key_id: str | None = None
    api_key_secret: str | None = None


class SMKConfig(BaseSettings):
    """Main SMK configuration.

    Supports environment variable overrides with SMK_ prefix.
    Nested values use double underscore delimiter.

    Examples:
        SMK_CONFIG_VERSION=2
        SMK_SOURCE__PLUGIN=terraform-cloud
        SMK_SPACELIFT__API_ENDPOINT=https://example.app.spacelift.io
    """

    model_config = SettingsConfigDict(
        env_prefix="SMK_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    config_version: int = 1
    plugins: PluginConfig = Field(default_factory=PluginConfig)
    source: SourceVendorConfig = Field(default_factory=SourceVendorConfig)
    spacelift: SpaceliftConfig = Field(default_factory=SpaceliftConfig)
