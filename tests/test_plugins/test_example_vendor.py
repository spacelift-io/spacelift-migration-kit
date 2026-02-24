"""Tests for example vendor plugin."""

from smk.plugins.example_vendor import smk_export_data, smk_get_post_apply_guidance, smk_post_apply_actions


def test_export_data_returns_mock_data() -> None:
    """smk_export_data returns dict with stacks, spaces, and policies."""
    result = smk_export_data({})
    assert "stacks" in result
    assert "spaces" in result
    assert "policies" in result
    assert len(result["stacks"]) > 0


def test_get_post_apply_guidance_returns_markdown() -> None:
    """smk_get_post_apply_guidance returns string containing expected heading."""
    guidance = smk_get_post_apply_guidance()
    assert "Post-Migration Steps" in guidance


def test_post_apply_actions_labels_stacks() -> None:
    """smk_post_apply_actions adds migration_actions to stack entities."""
    entities = [{"type": "stack", "id": "s-1"}]
    result = smk_post_apply_actions(entities)
    assert "migration_actions" in result[0]


def test_post_apply_actions_skips_non_stacks() -> None:
    """smk_post_apply_actions does not add migration_actions to non-stack entities."""
    entities = [{"type": "policy", "id": "p-1"}]
    result = smk_post_apply_actions(entities)
    assert "migration_actions" not in result[0]
