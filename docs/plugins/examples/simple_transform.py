"""Simple transformation plugin example.

This plugin demonstrates basic stack transformation by adding
labels and applying a naming convention.
"""

import pluggy

hookimpl = pluggy.HookimplMarker("smk")


@hookimpl
def smk_transform_stack(stack: dict) -> dict:
    """Add labels and apply naming convention.

    Args:
        stack: Stack entity from source vendor

    Returns:
        Transformed stack with labels and new name
    """
    # Preserve original name for reference
    original_name = stack.get("name", "unknown")

    # Apply naming convention
    environment = stack.get("environment", "dev")
    stack["name"] = f"{environment}-{original_name}"

    # Add standard labels
    if "labels" not in stack:
        stack["labels"] = []

    stack["labels"].extend(
        [
            "migrated",
            f"original-name:{original_name}",
            f"environment:{environment}",
        ]
    )

    # Ensure branch is set
    if "branch" not in stack:
        # Use main for production, develop for others
        stack["branch"] = "main" if environment == "prod" else "develop"

    return stack


@hookimpl
def smk_post_transform(transformed_data: dict) -> dict:
    """Log transformation summary.

    Args:
        transformed_data: All transformed entities

    Returns:
        Unmodified transformed data
    """
    stacks = transformed_data.get("stacks", [])
    print(f"Transformed {len(stacks)} stacks")  # noqa: T201
    print("Naming convention: {environment}-{name}")  # noqa: T201
    print("Labels added: migrated, original-name, environment")  # noqa: T201

    return transformed_data
