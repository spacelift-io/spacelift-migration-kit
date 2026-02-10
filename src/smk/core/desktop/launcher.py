"""Desktop launcher with availability detection."""


def is_desktop_available() -> bool:
    """Check if desktop mode is available.

    Returns:
        True if pywebview can be imported, False otherwise.
    """
    try:
        import webview  # noqa: F401

        return True
    except ImportError:
        return False
