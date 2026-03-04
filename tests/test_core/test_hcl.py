"""Tests for HCL serializer."""

from smk.core.hcl import batch_to_hcl, entity_to_hcl


def test_entity_to_hcl_basic() -> None:
    """Renders a simple resource block."""
    entity = {
        "resource_type": "spacelift_space",
        "resource_name": "org_my_company",
        "attributes": {
            "name": "my-company",
            "parent_space_id": "root",
        },
    }
    hcl = entity_to_hcl(entity)
    assert 'resource "spacelift_space" "org_my_company" {' in hcl
    assert '  name = "my-company"' in hcl
    assert '  parent_space_id = "root"' in hcl
    assert hcl.strip().endswith("}")


def test_entity_to_hcl_ref_unquoted() -> None:
    """$ref: values become bare TF references."""
    entity = {
        "resource_type": "spacelift_space",
        "resource_name": "proj_default",
        "attributes": {
            "name": "default",
            "parent_space_id": "$ref:spacelift_space.org_my_company.id",
        },
    }
    hcl = entity_to_hcl(entity)
    assert "  parent_space_id = spacelift_space.org_my_company.id" in hcl
    # Should NOT be quoted
    assert '"spacelift_space.org_my_company.id"' not in hcl


def test_entity_to_hcl_bool_values() -> None:
    """bool values become true/false."""
    entity = {
        "resource_type": "spacelift_stack",
        "resource_name": "ws_test",
        "attributes": {"autodeploy": True, "protect_from_deletion": False},
    }
    hcl = entity_to_hcl(entity)
    assert "  autodeploy = true" in hcl
    assert "  protect_from_deletion = false" in hcl


def test_entity_to_hcl_none_value() -> None:
    """None values become null."""
    entity = {
        "resource_type": "spacelift_stack",
        "resource_name": "ws_x",
        "attributes": {"branch": None},
    }
    hcl = entity_to_hcl(entity)
    assert "  branch = null" in hcl


def test_entity_to_hcl_int_value() -> None:
    """Integer values are rendered bare."""
    entity = {
        "resource_type": "spacelift_stack",
        "resource_name": "ws_x",
        "attributes": {"count": 42},
    }
    hcl = entity_to_hcl(entity)
    assert "  count = 42" in hcl


def test_entity_to_hcl_nested_dict() -> None:
    """Nested dicts become HCL blocks."""
    entity = {
        "resource_type": "spacelift_stack",
        "resource_name": "ws_x",
        "attributes": {
            "vcs_repo": {"identifier": "org/repo", "branch": "main"},
        },
    }
    hcl = entity_to_hcl(entity)
    assert "  vcs_repo {" in hcl


def test_entity_to_hcl_list_value() -> None:
    """List values are rendered as HCL list literals."""
    entity = {
        "resource_type": "spacelift_stack",
        "resource_name": "ws_x",
        "attributes": {"labels": ["prod", "api"]},
    }
    hcl = entity_to_hcl(entity)
    assert '"prod"' in hcl
    assert '"api"' in hcl


def test_batch_to_hcl_header() -> None:
    """batch_to_hcl includes batch header comment."""
    entities = [
        {
            "resource_type": "spacelift_space",
            "resource_name": "org_x",
            "attributes": {"name": "x", "parent_space_id": "root"},
        }
    ]
    hcl = batch_to_hcl(3, entities)
    assert "# SMK Batch 3" in hcl


def test_batch_to_hcl_multiple_entities() -> None:
    """batch_to_hcl includes all entity blocks."""
    entities = [
        {
            "resource_type": "spacelift_space",
            "resource_name": "org_a",
            "attributes": {"name": "a", "parent_space_id": "root"},
        },
        {
            "resource_type": "spacelift_space",
            "resource_name": "proj_b",
            "attributes": {"name": "b", "parent_space_id": "$ref:spacelift_space.org_a.id"},
        },
    ]
    hcl = batch_to_hcl(1, entities)
    assert '"org_a"' in hcl
    assert '"proj_b"' in hcl
    assert "spacelift_space.org_a.id" in hcl


def test_batch_to_hcl_ends_with_newline() -> None:
    """HCL file ends with newline."""
    hcl = batch_to_hcl(1, [{"resource_type": "t", "resource_name": "r", "attributes": {}}])
    assert hcl.endswith("\n")


def test_entity_to_hcl_deeply_nested_dict() -> None:
    """Deeply nested dicts become nested HCL blocks."""
    entity = {
        "resource_type": "spacelift_stack",
        "resource_name": "ws_x",
        "attributes": {
            "vcs_repo": {"branch": "main", "tags": {"env": "prod"}},
        },
    }
    hcl = entity_to_hcl(entity)
    assert "vcs_repo" in hcl
    assert "branch" in hcl
    assert "tags" in hcl


def test_hcl_value_dict() -> None:
    """Dict passed directly to _hcl_value returns an HCL block."""
    from smk.core.hcl import _hcl_value

    result = _hcl_value({"key": "val"})
    assert "key" in result
    assert "val" in result


def test_hcl_value_float() -> None:
    """Float values are rendered bare."""
    from smk.core.hcl import _hcl_value

    assert _hcl_value(3.14) == "3.14"


def test_hcl_value_unknown_type_fallback() -> None:
    """Unknown types fall back to quoted string representation."""
    from smk.core.hcl import _hcl_value

    class Custom:
        def __str__(self) -> str:
            return "custom"

    assert _hcl_value(Custom()) == '"custom"'
