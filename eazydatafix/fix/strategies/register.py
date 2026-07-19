"""
Built-in strategy plugin registration.

This module is responsible for registering all built-in
missing value strategies with the EasyDataFix plugin registry.

It intentionally contains no business logic.
Its only responsibility is plugin registration.
"""

from eazydatafix.plugins.registry import PluginRegistry

from eazydatafix.fix.strategies.mean import MeanStrategy
from eazydatafix.fix.strategies.median import MedianStrategy
from eazydatafix.fix.strategies.mode import ModeStrategy
from eazydatafix.fix.strategies.smart import SmartStrategy
from eazydatafix.fix.strategies.drop import DropStrategy


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
