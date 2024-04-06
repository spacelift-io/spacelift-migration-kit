import pytest


@pytest.fixture(scope="module")
def vcr_config():
    return {
        "filter_headers": [("Authorization", "[REDACTED]")],
        "record_mode": "once",
    }
