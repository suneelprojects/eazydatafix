from abc import ABC, abstractmethod

import pandas as pd


class MissingValueStrategy(ABC):
    """
    Base class for missing value handling strategies.
    """

    @abstractmethod
    def apply(
        self,
        df: pd.DataFrame,
        applied_fixes: list[str],
        columns: list[str] | None = None,
    ) -> pd.DataFrame:
        """
        Apply the missing value strategy.
        """
        pass
