"""Tests for Spacelift source plugin."""

from smk.plugins.spacelift import smk_export_data, smk_get_source_info


def test_get_source_info() -> None:
    """smk_get_source_info returns expected plugin metadata."""
    info = smk_get_source_info()
    assert info["plugin_id"] == "spacelift"
    assert "display_name" in info
    assert "fields" in info


def test_export_data_returns_empty_stubs() -> None:
    """smk_export_data returns empty stubs for spacelift source."""
    result = smk_export_data({"source_plugin": "spacelift"})
    assert result == {"policies": [], "spaces": [], "stacks": []}


def test_export_data_skips_non_spacelift_source() -> None:
    """smk_export_data returns None for non-spacelift sources."""
    result = smk_export_data({"source_plugin": "other"})
    assert result is None
