from abc import ABC, abstractmethod

import pandas as pd


class FixStrategy(ABC):
    """
    Base contract for all automatic data cleaning strategies.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Name of the strategy.
        """
        raise NotImplementedError

    @abstractmethod
    def apply(self, df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
        """
        Apply the cleaning strategy.

        Returns:
            A cleaned DataFrame and a list of applied fixes.
        """
        raise NotImplementedError
