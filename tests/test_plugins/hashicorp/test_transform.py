"""Tests for smk_transform_entity in the HashiCorp plugin."""

import smk.plugins.hashicorp as plugin


def test_transform_org_returns_spacelift_space() -> None:
    """Organizations transform to spacelift_space with parent_space_id=root."""
    entity = {"id": "org-1", "name": "my-org"}
    result = plugin.smk_transform_entity(entity_type="organizations", entity=entity, source_plugin="hashicorp")
    assert result is not None
    assert result["resource_type"] == "spacelift_space"
    assert result["resource_name"] == "my_org"
    assert result["attributes"]["parent_space_id"] == "root"
    assert result["attributes"]["name"] == "my-org"


def test_transform_project_with_parent_ref() -> None:
    """Projects with parent include org qualifier in resource name."""
    entity = {
        "id": "prj-1",
        "name": "default",
        "_smk_parent_hcl_resource_name": "spacelift_space.my_org",
    }
    result = plugin.smk_transform_entity(entity_type="projects", entity=entity, source_plugin="hashicorp")
    assert result is not None
    assert result["resource_type"] == "spacelift_space"
    assert result["resource_name"] == "my_org_default"
    assert result["attributes"]["parent_space_id"] == "$ref:spacelift_space.my_org.id"


def test_transform_project_without_parent_defaults_root() -> None:
    """Projects without parent use name only and default to root."""
    entity = {"id": "prj-1", "name": "default"}
    result = plugin.smk_transform_entity(entity_type="projects", entity=entity, source_plugin="hashicorp")
    assert result is not None
    assert result["resource_name"] == "default"
    assert result["attributes"]["parent_space_id"] == "root"


def test_transform_workspace_with_parent_ref() -> None:
    """Workspaces with parent include parent qualifier in resource name."""
    entity = {
        "id": "ws-1",
        "name": "prod-api",
        "_smk_parent_hcl_resource_name": "spacelift_space.my_org_default",
    }
    result = plugin.smk_transform_entity(entity_type="workspaces", entity=entity, source_plugin="hashicorp")
    assert result is not None
    assert result["resource_type"] == "spacelift_stack"
    assert result["resource_name"] == "my_org_default_prod_api"
    assert result["attributes"]["space_id"] == "$ref:spacelift_space.my_org_default.id"


def test_transform_workspace_without_parent() -> None:
    """Workspaces without parent use name only and omit space_id."""
    entity = {"id": "ws-1", "name": "prod-api"}
    result = plugin.smk_transform_entity(entity_type="workspaces", entity=entity, source_plugin="hashicorp")
    assert result is not None
    assert result["resource_name"] == "prod_api"
    assert "space_id" not in result["attributes"]


def test_transform_workspace_name_collision_different_parents() -> None:
    """Two workspaces with the same name under different parents get distinct resource names."""
    entity_a = {"id": "ws-a", "name": "prod", "_smk_parent_hcl_resource_name": "spacelift_space.acme_frontend"}
    entity_b = {"id": "ws-b", "name": "prod", "_smk_parent_hcl_resource_name": "spacelift_space.acme_backend"}
    result_a = plugin.smk_transform_entity(entity_type="workspaces", entity=entity_a, source_plugin="hashicorp")
    result_b = plugin.smk_transform_entity(entity_type="workspaces", entity=entity_b, source_plugin="hashicorp")
    assert result_a is not None and result_b is not None
    assert result_a["resource_name"] != result_b["resource_name"]
    assert result_a["resource_name"] == "acme_frontend_prod"
    assert result_b["resource_name"] == "acme_backend_prod"


def test_transform_workspace_description() -> None:
    """Non-empty description is mapped."""
    entity = {"id": "ws-1", "name": "prod-api", "description": "My stack"}
    result = plugin.smk_transform_entity(entity_type="workspaces", entity=entity, source_plugin="hashicorp")
    assert result is not None
    assert result["attributes"]["description"] == "My stack"


def test_transform_workspace_empty_description_omitted() -> None:
    """Empty description is not included."""
    entity = {"id": "ws-1", "name": "prod-api", "description": ""}
    result = plugin.smk_transform_entity(entity_type="workspaces", entity=entity, source_plugin="hashicorp")
    assert result is not None
    assert "description" not in result["attributes"]


def test_transform_workspace_autodeploy() -> None:
    """auto_apply maps to autodeploy."""
    entity = {"id": "ws-1", "name": "prod-api", "auto_apply": True}
    result = plugin.smk_transform_entity(entity_type="workspaces", entity=entity, source_plugin="hashicorp")
    assert result is not None
    assert result["attributes"]["autodeploy"] is True


def test_transform_workspace_autodeploy_false() -> None:
    """auto_apply=False maps to autodeploy=False."""
    entity = {"id": "ws-1", "name": "prod-api", "auto_apply": False}
    result = plugin.smk_transform_entity(entity_type="workspaces", entity=entity, source_plugin="hashicorp")
    assert result is not None
    assert result["attributes"]["autodeploy"] is False


def test_transform_workspace_terraform_version() -> None:
    """terraform_version is mapped."""
    entity = {"id": "ws-1", "name": "prod-api", "terraform_version": "1.5.0"}
    result = plugin.smk_transform_entity(entity_type="workspaces", entity=entity, source_plugin="hashicorp")
    assert result is not None
    assert result["attributes"]["terraform_version"] == "1.5.0"


def test_transform_workspace_project_root() -> None:
    """working_directory maps to project_root with trailing slash stripped."""
    entity = {"id": "ws-1", "name": "prod-api", "working_directory": "infra/prod/"}
    result = plugin.smk_transform_entity(entity_type="workspaces", entity=entity, source_plugin="hashicorp")
    assert result is not None
    assert result["attributes"]["project_root"] == "infra/prod"


def test_transform_workspace_empty_working_directory_omitted() -> None:
    """Empty working_directory is not included."""
    entity = {"id": "ws-1", "name": "prod-api", "working_directory": ""}
    result = plugin.smk_transform_entity(entity_type="workspaces", entity=entity, source_plugin="hashicorp")
    assert result is not None
    assert "project_root" not in result["attributes"]


def test_transform_workspace_vcs_repo() -> None:
    """vcs_repo.identifier splits into namespace and repository; branch mapped if non-empty."""
    entity = {
        "id": "ws-1",
        "name": "prod-api",
        "vcs_repo": {"identifier": "my-org/my-repo", "branch": "main"},
    }
    result = plugin.smk_transform_entity(entity_type="workspaces", entity=entity, source_plugin="hashicorp")
    assert result is not None
    assert result["attributes"]["namespace"] == "my-org"
    assert result["attributes"]["repository"] == "my-repo"
    assert result["attributes"]["branch"] == "main"


def test_transform_workspace_vcs_empty_branch_omitted() -> None:
    """Empty branch is not included."""
    entity = {
        "id": "ws-1",
        "name": "prod-api",
        "vcs_repo": {"identifier": "my-org/my-repo", "branch": ""},
    }
    result = plugin.smk_transform_entity(entity_type="workspaces", entity=entity, source_plugin="hashicorp")
    assert result is not None
    assert "branch" not in result["attributes"]


def test_transform_workspace_vcs_identifier_no_slash() -> None:
    """vcs_repo.identifier without '/' maps to repository only."""
    entity = {
        "id": "ws-1",
        "name": "prod-api",
        "vcs_repo": {"identifier": "my-repo", "branch": ""},
    }
    result = plugin.smk_transform_entity(entity_type="workspaces", entity=entity, source_plugin="hashicorp")
    assert result is not None
    assert result["attributes"]["repository"] == "my-repo"
    assert "namespace" not in result["attributes"]


def test_transform_workspace_vcs_empty_identifier_omitted() -> None:
    """vcs_repo with empty identifier maps neither namespace nor repository."""
    entity = {"id": "ws-1", "name": "prod-api", "vcs_repo": {"identifier": "", "branch": ""}}
    result = plugin.smk_transform_entity(entity_type="workspaces", entity=entity, source_plugin="hashicorp")
    assert result is not None
    assert "namespace" not in result["attributes"]
    assert "repository" not in result["attributes"]


def test_transform_workspace_no_vcs_repo_omits_vcs_attrs() -> None:
    """No vcs_repo means no namespace/repository/branch."""
    entity = {"id": "ws-1", "name": "prod-api"}
    result = plugin.smk_transform_entity(entity_type="workspaces", entity=entity, source_plugin="hashicorp")
    assert result is not None
    assert "namespace" not in result["attributes"]
    assert "repository" not in result["attributes"]
    assert "branch" not in result["attributes"]


def test_transform_workspace_labels() -> None:
    """tag_names map to labels."""
    entity = {"id": "ws-1", "name": "prod-api", "tag_names": ["team:platform", "env:prod"]}
    result = plugin.smk_transform_entity(entity_type="workspaces", entity=entity, source_plugin="hashicorp")
    assert result is not None
    assert result["attributes"]["labels"] == ["team:platform", "env:prod"]


def test_transform_workspace_empty_labels_omitted() -> None:
    """Empty tag_names list is not included."""
    entity = {"id": "ws-1", "name": "prod-api", "tag_names": []}
    result = plugin.smk_transform_entity(entity_type="workspaces", entity=entity, source_plugin="hashicorp")
    assert result is not None
    assert "labels" not in result["attributes"]


def test_transform_workspace_json_api_format() -> None:
    """JSON API format (attributes nested under 'attributes' key) is handled."""
    entity = {
        "id": "ws-1",
        "attributes": {
            "name": "prod-api",
            "description": "JSON API workspace",
            "auto-apply": True,
            "terraform-version": "1.6.0",
            "working-directory": "modules/app",
            "vcs-repo": {"identifier": "org/repo", "branch": "develop"},
            "tag-names": ["env:staging"],
        },
    }
    result = plugin.smk_transform_entity(entity_type="workspaces", entity=entity, source_plugin="hashicorp")
    assert result is not None
    assert result["attributes"]["description"] == "JSON API workspace"
    assert result["attributes"]["autodeploy"] is True
    assert result["attributes"]["terraform_version"] == "1.6.0"
    assert result["attributes"]["project_root"] == "modules/app"
    assert result["attributes"]["namespace"] == "org"
    assert result["attributes"]["repository"] == "repo"
    assert result["attributes"]["branch"] == "develop"
    assert result["attributes"]["labels"] == ["env:staging"]


def test_transform_wrong_plugin_returns_none() -> None:
    """Returns None for non-hashicorp plugins."""
    entity = {"id": "org-1", "name": "x"}
    result = plugin.smk_transform_entity(entity_type="organizations", entity=entity, source_plugin="other")
    assert result is None


def test_transform_unknown_entity_type_returns_none() -> None:
    """Returns None for unknown entity types."""
    entity = {"id": "x", "name": "x"}
    result = plugin.smk_transform_entity(entity_type="unknown_type", entity=entity, source_plugin="hashicorp")
    assert result is None


def test_resource_name_sanitizes_special_chars() -> None:
    """_resource_name sanitizes special characters and strips trailing underscores."""
    from smk.plugins.hashicorp import _resource_name

    assert _resource_name("My Company!") == "my_company"
    result = _resource_name("  test  ")
    assert result == "test"


def test_resource_name_empty_fallback() -> None:
    """_resource_name uses 'unknown' for empty names."""
    from smk.plugins.hashicorp import _resource_name

    result = _resource_name("!!!")
    assert result == "unknown"


def test_transform_org_resource_name_sanitized() -> None:
    """Organization resource name is properly sanitized."""
    entity = {"id": "org-1", "name": "My Company!"}
    result = plugin.smk_transform_entity(entity_type="organizations", entity=entity, source_plugin="hashicorp")
    assert result is not None
    assert " " not in result["resource_name"]
    assert "!" not in result["resource_name"]
