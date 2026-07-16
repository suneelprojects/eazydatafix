"""
Built-in strategy plugin registration.

This module is responsible for registering all built-in
missing value strategies with the EasyDataFix plugin registry.

It intentionally contains no business logic.
Its only responsibility is plugin registration.
"""

from easydatafix.plugins.registry import PluginRegistry

from easydatafix.fix.strategies.mean import MeanStrategy
from easydatafix.fix.strategies.median import MedianStrategy
from easydatafix.fix.strategies.mode import ModeStrategy
from easydatafix.fix.strategies.smart import SmartStrategy
from easydatafix.fix.strategies.drop import DropStrategy


def register_plugins(registry: PluginRegistry) -> None:
    """
    Register all built-in missing value strategies.

    Parameters
    ----------
    registry : PluginRegistry
        The application plugin registry.
    """

    registry.register(
        category="strategy",
        plugin=MeanStrategy,
    )

    registry.register(
        category="strategy",
        plugin=MedianStrategy,
    )

    registry.register(
        category="strategy",
        plugin=ModeStrategy,
    )

    registry.register(
        category="strategy",
        plugin=SmartStrategy,
    )

    registry.register(
        category="strategy",
        plugin=DropStrategy,
    )
