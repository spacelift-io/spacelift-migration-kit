"""Example vendor plugin.

This is a reference implementation demonstrating how to create a built-in
vendor plugin for SMK. Vendor plugins handle:

1. Exporting data from source infrastructure management platform
2. Providing post-apply guidance for manual migration steps
3. Performing automated post-apply actions

This example uses mock data to demonstrate the patterns without requiring
an actual vendor API connection.
"""

import pluggy

hookimpl = pluggy.HookimplMarker("smk")


@hookimpl
def smk_export_data(vendor_config: dict) -> dict:  # noqa: ARG001
    """Export infrastructure data from example vendor.

    In a real vendor plugin, this would:
    - Authenticate with vendor API
    - Fetch all stacks/workspaces
    - Fetch associated resources (VCS, policies, etc.)
    - Return structured data for transformation

    Args:
        vendor_config: Configuration from source.config section

    Returns:
        Dictionary containing exported entities
    """
    # Mock data representing a typical export structure
    # In real implementation, vendor_config would be used for API authentication
    return {
        "stacks": [
            {
                "id": "stack-1",
                "name": "production-api",
                "description": "Production API infrastructure",
                "environment": "prod",
                "repository": "https://github.com/example/infrastructure",
                "branch": "main",
                "terraform_version": "1.5.0",
                "labels": ["api", "production"],
                "variables": {
                    "AWS_REGION": {"value": "us-east-1", "sensitive": False},
                    "API_KEY": {"value": "***", "sensitive": True},
                },
                "policies": ["require-approval", "cost-limit"],
            },
            {
                "id": "stack-2",
                "name": "staging-api",
                "description": "Staging API infrastructure",
                "environment": "staging",
                "repository": "https://github.com/example/infrastructure",
                "branch": "develop",
                "terraform_version": "1.5.0",
                "labels": ["api", "staging"],
                "variables": {
                    "AWS_REGION": {"value": "us-west-2", "sensitive": False},
                },
                "policies": ["auto-approve"],
            },
        ],
        "spaces": [
            {
                "id": "space-1",
                "name": "engineering",
                "description": "Engineering team workspace",
            },
        ],
        "policies": [
            {
                "id": "policy-1",
                "name": "require-approval",
                "type": "approval",
                "rules": ["require at least 1 approval"],
            },
            {
                "id": "policy-2",
                "name": "cost-limit",
                "type": "plan",
                "rules": ["cost increase < $1000"],
            },
            {
                "id": "policy-3",
                "name": "auto-approve",
                "type": "approval",
                "rules": ["auto-approve if no resource changes"],
            },
        ],
    }


@hookimpl
def smk_get_post_apply_guidance() -> str:
    """Provide guidance for manual post-migration steps.

    Returns:
        Markdown-formatted guidance for user
    """
    return """
## Post-Migration Steps for Example Vendor

After the migration is complete, perform these manual steps:

### 1. Verify Stack State

- Log into Example Vendor dashboard
- Verify all stacks show "migrated" status
- Check that no runs are in progress

### 2. Update Webhooks

If you have webhooks configured in Example Vendor:

```bash
# List current webhooks
example-vendor webhooks list

# Delete old webhooks
example-vendor webhooks delete <webhook-id>
```

### 3. Archive Old Stacks

Once verified in Spacelift, archive the old stacks:

```bash
# Archive all migrated stacks
example-vendor stacks archive --label migrated
```

### 4. Update Documentation

- Update team documentation with new Spacelift URLs
- Update runbooks to reference Spacelift instead of Example Vendor
- Notify team members of the migration

### 5. Cleanup

After 30 days, if no issues:

```bash
# Permanently delete archived stacks
example-vendor stacks delete --archived
```

For questions, contact the platform team.
"""


@hookimpl
def smk_post_apply_actions(entities: list[dict]) -> list[dict]:
    """Perform automated actions after Spacelift apply completes.

    In a real vendor plugin, this might:
    - Mark source stacks as "migrated"
    - Lock source stacks to prevent changes
    - Add migration metadata/labels
    - Trigger notifications

    Args:
        entities: List of entities that were successfully applied

    Returns:
        Updated entities with action results
    """
    # In a real implementation, would make API calls to vendor
    for entity in entities:
        if entity.get("type") == "stack":
            # Mock: Add metadata showing actions that would be taken
            entity["migration_actions"] = {
                "labeled": True,
                "locked": True,
                "notification_sent": True,
                "archived": False,  # User must manually archive after verification
            }

    return entities
