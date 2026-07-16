"""
Default plugin registry for EasyDataFix.

This module owns the application's shared plugin registry.

Built-in plugins are registered lazily to avoid circular imports
during package initialization.
"""

from easydatafix.plugins.registry import PluginRegistry

default_registry = PluginRegistry()


def register_builtin_plugins() -> PluginRegistry:
    """
    Register all built-in EasyDataFix plugins.

    Returns
    -------
    PluginRegistry
        The initialized application registry.
    """

    # Lazy imports prevent circular dependencies.
    from easydatafix.fix.strategies.register import (
        register_plugins as register_strategy_plugins,
    )

    register_strategy_plugins(default_registry)

    return default_registry
