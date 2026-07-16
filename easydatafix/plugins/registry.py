"""
Generic plugin registry for EasyDataFix.

The registry stores plugins by category while remaining completely
agnostic about plugin behavior.
"""

from collections import defaultdict


class PluginRegistry:
    """
    Generic registry for EasyDataFix plugins.
    """

    def __init__(self):
        self._plugins = defaultdict(dict)

    def register(self, category: str, plugin):
        """
        Register a plugin under a category.

        Plugins may be classes or instances.
        """

        name = getattr(plugin, "name", None)

        if not name:
            raise ValueError(
                "Plugins must define a non-empty 'name' attribute."
            )

        if name in self._plugins[category]:
            raise ValueError(
                f"Plugin '{name}' is already registered "
                f"under category '{category}'."
            )

        self._plugins[category][name] = plugin

    def find(self, category: str, name: str):
        """
        Find a plugin by category and name.
        """

        return self._plugins.get(category, {}).get(name)

    def all(self, category: str):
        """
        Return every plugin registered under a category.
        """

        return list(self._plugins.get(category, {}).values())

    def categories(self):
        """
        Return every registered category.
        """

        return list(self._plugins.keys())