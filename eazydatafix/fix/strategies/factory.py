from eazydatafix.fix.strategies.base import MissingValueStrategy
from eazydatafix.fix.strategies.drop import DropStrategy
from eazydatafix.fix.strategies.mean import MeanStrategy
from eazydatafix.fix.strategies.median import MedianStrategy
from eazydatafix.fix.strategies.mode import ModeStrategy
from eazydatafix.fix.strategies.smart import SmartStrategy


class StrategyFactory:
    """
    Factory for creating missing value strategies.
    """

    @staticmethod
    def create(strategy: str) -> MissingValueStrategy:

        strategy = strategy.lower()

        strategies = {
            "smart": SmartStrategy,
            "mean": MeanStrategy,
            "median": MedianStrategy,
            "mode": ModeStrategy,
            "drop": DropStrategy,
        }

        if strategy not in strategies:
            raise ValueError(
                f"Unsupported missing value strategy: {strategy}"
            )

        return strategies[strategy]()
