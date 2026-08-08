"""
EazyDataFix Plugin Architecture.

This package exposes the public plugin interfaces used
throughout EazyDataFix.

Plugin registration is intentionally NOT performed here to
avoid circular imports during application startup.
"""

from .base import Plugin
from .registry import PluginRegistry


def register_workflow_plugin(plugin: object) -> None:
    """Register a lightweight deterministic workflow extension."""
    from eazydatafix.plugins.defaults import default_registry

    default_registry.register(category="workflow", plugin=plugin)


__all__ = [
    "Plugin",
    "PluginRegistry",
    "register_workflow_plugin",
]
