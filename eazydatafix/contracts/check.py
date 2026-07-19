from abc import ABC, abstractmethod

import pandas as pd


class Check(ABC):
    """
    Base contract for all assessment checks.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Name of the check.
        """
        raise NotImplementedError

    @abstractmethod
    def evaluate(self, df: pd.DataFrame):
        """
        Execute the check against a DataFrame.
        """
        raise NotImplementedError
