"""Tests for config models."""

import pytest

from smk.core.config.models import PluginConfig, SMKConfig, SourceVendorConfig, SpaceliftConfig


class TestPluginConfig:
    """Tests for PluginConfig model."""

    def test_defaults(self):
        """Plugin config should have empty enabled list by default."""
        config = PluginConfig()
        assert config.enabled == []

    def test_with_plugins(self):
        """Plugin config should accept enabled plugins."""
        config = PluginConfig(enabled=["plugin-a", "plugin-b"])
        assert config.enabled == ["plugin-a", "plugin-b"]


class TestSourceVendorConfig:
    """Tests for SourceVendorConfig model."""

    def test_defaults(self):
        """Source config should have None plugin and empty credentials."""
        config = SourceVendorConfig()
        assert config.plugin is None
        assert config.credentials == {}

    def test_with_values(self):
        """Source config should accept plugin and credentials."""
        config = SourceVendorConfig(
            plugin="terraform-cloud",
            credentials={"token": "secret123"},
        )
        assert config.plugin == "terraform-cloud"
        assert config.credentials == {"token": "secret123"}


class TestSpaceliftConfig:
    """Tests for SpaceliftConfig model."""

    def test_defaults(self):
        """Spacelift config should have all None values by default."""
        config = SpaceliftConfig()
        assert config.api_endpoint is None
        assert config.api_key_id is None
        assert config.api_key_secret is None

    def test_with_values(self):
        """Spacelift config should accept all values."""
        config = SpaceliftConfig(
            api_endpoint="https://example.app.spacelift.io",
            api_key_id="key123",
            api_key_secret="secret456",
        )
        assert config.api_endpoint == "https://example.app.spacelift.io"
        assert config.api_key_id == "key123"
        assert config.api_key_secret == "secret456"


class TestSMKConfig:
    """Tests for SMKConfig model."""

    def test_defaults(self):
        """SMK config should have sensible defaults."""
        config = SMKConfig()
        assert config.config_version == 1
        assert config.plugins.enabled == []
        assert config.source.plugin is None
        assert config.spacelift.api_endpoint is None

    def test_with_nested_values(self):
        """SMK config should accept nested values."""
        config = SMKConfig(
            config_version=2,
            plugins=PluginConfig(enabled=["plugin-a"]),
            source=SourceVendorConfig(plugin="terraform-cloud"),
            spacelift=SpaceliftConfig(api_endpoint="https://example.app.spacelift.io"),
        )
        assert config.config_version == 2
        assert config.plugins.enabled == ["plugin-a"]
        assert config.source.plugin == "terraform-cloud"
        assert config.spacelift.api_endpoint == "https://example.app.spacelift.io"

    def test_env_override_top_level(self, monkeypatch: pytest.MonkeyPatch):
        """SMK config should support env var overrides for top-level fields."""
        monkeypatch.setenv("SMK_CONFIG_VERSION", "99")
        config = SMKConfig()
        assert config.config_version == 99

    def test_env_override_nested(self, monkeypatch: pytest.MonkeyPatch):
        """SMK config should support env var overrides for nested fields."""
        monkeypatch.setenv("SMK_SOURCE__PLUGIN", "env-plugin")
        monkeypatch.setenv("SMK_SPACELIFT__API_ENDPOINT", "https://env.spacelift.io")
        config = SMKConfig()
        assert config.source.plugin == "env-plugin"
        assert config.spacelift.api_endpoint == "https://env.spacelift.io"

    def test_extra_fields_ignored(self):
        """SMK config should ignore extra fields."""
        # pydantic-settings with extra="ignore" should ignore unknown fields
        # Test by loading from dict with extra fields via model_validate
        data = {"config_version": 1, "unknown_field": "ignored"}
        config = SMKConfig.model_validate(data)
        assert not hasattr(config, "unknown_field")
