"""
EazyDataFix Plugin Architecture.

This package exposes the public plugin interfaces used
throughout EazyDataFix.

Plugin registration is intentionally NOT performed here to
avoid circular imports during application startup.
"""

from .base import Plugin
from .registry import PluginRegistry

__all__ = [
    "Plugin",
    "PluginRegistry",
]
