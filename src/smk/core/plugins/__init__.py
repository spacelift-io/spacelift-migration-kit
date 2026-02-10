"""SMK plugin system.

Provides pluggy-based plugin architecture with deployment-mode-aware dependency management.
"""

from smk.core.plugins.manager import SMKPluginManager

__all__ = ["SMKPluginManager"]
