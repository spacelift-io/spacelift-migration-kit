"""Tests for plugin configuration models."""

from smk.core.plugins.models import ConfigField, ConfigFieldDependency, SourcePluginInfo


def test_config_field_dependency_fields() -> None:
    """ConfigFieldDependency stores field and value."""
    dep = ConfigFieldDependency(field="product", value="enterprise")
    assert dep.field == "product"
    assert dep.value == "enterprise"


def test_config_field_defaults() -> None:
    """ConfigField has sensible defaults."""
    field = ConfigField(key="token", label="API Token", type="password")
    assert field.required is True
    assert field.depends_on is None
    assert field.help_text == ""
    assert field.options == []
    assert field.placeholder == ""


def test_config_field_with_all_fields() -> None:
    """ConfigField accepts all optional fields."""
    dep = ConfigFieldDependency(field="mode", value="advanced")
    field = ConfigField(
        key="host",
        label="Host",
        type="url",
        required=False,
        depends_on=dep,
        help_text="Enter host URL",
        options=[{"label": "A", "value": "a"}],
        placeholder="https://example.com",
    )
    assert field.key == "host"
    assert field.depends_on == dep
    assert len(field.options) == 1


def test_source_plugin_info_defaults() -> None:
    """SourcePluginInfo has correct defaults."""
    info = SourcePluginInfo(display_name="Test", plugin_id="test")
    assert info.description == ""
    assert info.fields == []


def test_source_plugin_info_with_fields() -> None:
    """SourcePluginInfo stores fields list."""
    field = ConfigField(key="token", label="Token", type="password")
    info = SourcePluginInfo(
        display_name="Test Plugin",
        plugin_id="test",
        description="A test plugin",
        fields=[field],
    )
    assert info.display_name == "Test Plugin"
    assert len(info.fields) == 1
