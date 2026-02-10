"""Plugin dependency management with dual-mode strategy."""

import subprocess
import sys
from pathlib import Path

from smk.core.config.paths import get_plugin_deps_dir
from smk.core.plugins.cache import PluginCache


class PluginDependencyManager:
    """Manages plugin dependencies with deployment-mode-aware strategy.

    In development mode: Verifies dependencies and shows helpful errors.
    In bundled mode: Auto-installs dependencies to isolated directory.
    """

    def __init__(self, cache: PluginCache, is_bundled: bool) -> None:
        """Initialize dependency manager.

        Args:
            cache: Plugin cache instance.
            is_bundled: True if running from PyInstaller bundle.
        """
        self.cache = cache
        self.is_bundled = is_bundled
        self.deps_dir = get_plugin_deps_dir()

    def check_dependencies(self, plugin_path: Path) -> tuple[bool, list[str]]:
        """Check if plugin has dependencies and if they're installed.

        Args:
            plugin_path: Path to plugin directory or file.

        Returns:
            Tuple of (has_dependencies, missing_packages).
        """
        requirements = self._get_requirements(plugin_path)
        if not requirements:
            return False, []

        # Check cache first
        if self.cache.is_dependencies_installed(plugin_path):
            return True, []

        # Verify each requirement
        missing = []
        for req in requirements:
            package_name = self._extract_package_name(req)
            if not self._is_package_available(package_name):
                missing.append(req)

        return True, missing

    def handle_dependencies(self, plugin_path: Path) -> tuple[bool, str | None]:
        """Handle plugin dependencies based on deployment mode.

        Args:
            plugin_path: Path to plugin.

        Returns:
            Tuple of (success, error_message).
        """
        has_deps, missing = self.check_dependencies(plugin_path)

        if not has_deps or not missing:
            return True, None

        if self.is_bundled:
            # Bundled mode: Auto-install
            return self._install_dependencies(plugin_path, missing)
        else:
            # Development mode: Show helpful error
            return False, self._format_dev_mode_error(missing)

    def _extract_package_name(self, requirement: str) -> str:
        """Extract package name from requirement string.

        Args:
            requirement: Requirement string (e.g., 'boto3>=1.26.0').

        Returns:
            Package name.
        """
        # Strip version specifiers
        for sep in ["==", ">=", "<=", "!=", "~=", ">", "<"]:
            if sep in requirement:
                return requirement.split(sep)[0].strip()
        return requirement.strip()

    def _format_dev_mode_error(self, missing: list[str]) -> str:
        """Format helpful error message for development mode.

        Args:
            missing: List of missing package requirements.

        Returns:
            Formatted error message.
        """
        packages = " ".join(missing)
        return (
            f"Missing dependencies: {', '.join(missing)}\n\n"
            f"Install with: uv add {packages}\n"
            f"Or with pip: pip install {packages}"
        )

    def _get_requirements(self, plugin_path: Path) -> list[str]:
        """Get requirements from plugin.

        Args:
            plugin_path: Path to plugin directory or file.

        Returns:
            List of requirement strings.
        """
        # Check for requirements.txt
        if plugin_path.is_file():
            req_file = plugin_path.parent / "requirements.txt"
        else:
            req_file = plugin_path / "requirements.txt"

        if not req_file.exists():
            return []

        try:
            return [
                line.strip() for line in req_file.read_text().splitlines() if line.strip() and not line.startswith("#")
            ]
        except OSError:
            return []

    def _install_dependencies(self, plugin_path: Path, requirements: list[str]) -> tuple[bool, str | None]:
        """Install dependencies to isolated directory (bundled mode only).

        Args:
            plugin_path: Path to plugin.
            requirements: List of requirement strings.

        Returns:
            Tuple of (success, error_message).
        """
        self.deps_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Install each requirement to isolated directory
            for req in requirements:
                subprocess.run(  # noqa: S603
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "--target",
                        str(self.deps_dir),
                        "--no-warn-script-location",
                        req,
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )

            # Add deps directory to sys.path if not already there
            if str(self.deps_dir) not in sys.path:
                sys.path.insert(0, str(self.deps_dir))

            # Mark as installed in cache
            self.cache.set_dependencies_installed(plugin_path, True)

            return True, None

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to install dependencies: {e.stderr}"
            return False, error_msg

    def _is_package_available(self, package_name: str) -> bool:
        """Check if package is available for import.

        Args:
            package_name: Package name to check.

        Returns:
            True if package can be imported.
        """
        try:
            __import__(package_name)
            return True
        except ImportError:
            return False
