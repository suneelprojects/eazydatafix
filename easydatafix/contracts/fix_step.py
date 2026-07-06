from abc import ABC, abstractmethod

import pandas as pd

from easydatafix.models.fix_config import FixConfig


class FixStep(ABC):
    """
    Base class for every cleaning step.
    """

    @abstractmethod
    def run(
        self,
        df: pd.DataFrame,
        config: FixConfig,
        applied_fixes: list[str],
    ) -> pd.DataFrame:
        """
        Execute the cleaning step.
        """
        pass
