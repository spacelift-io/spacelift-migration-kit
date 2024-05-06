import pytest

from spacemk import terraform_version_to_semver


@pytest.mark.parametrize(
    ("version", "expected_version"),
    [
        (">= 1.3.0, <1.6.0", "1.5.7"),
        ("~> 1.3.9", "1.3.9"),
        ("~> 1.5.0", "1.5.0"),
        ("~>1.5.7", "1.5.7"),
        ("1.5.2", "1.5.2"),
        ("1.6.3", "1.6.3"),
        ("latest", "1.5.7"),
        (None, "1.5.7"),
    ],
)
def test_terraform_version_to_semver(version: str | None, expected_version: str) -> None:
    actual_version = terraform_version_to_semver(version)
    assert actual_version == expected_version
