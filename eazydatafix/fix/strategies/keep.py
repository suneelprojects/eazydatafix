import pandas as pd

from eazydatafix.fix.strategies.base import MissingValueStrategy
from eazydatafix.plugins import Plugin


class KeepStrategy(Plugin, MissingValueStrategy):
    """Preserve missing values for a later leakage-safe workflow stage."""

    name = "keep"
    version = "1.0.0"
    author = "EazyDataFix"
    description = "Keep missing values unchanged."

    def apply(
        self,
        df: pd.DataFrame,
        applied_fixes: list[str],
        columns: list[str] | None = None,
    ) -> pd.DataFrame:
        """Return the dataset unchanged without recording a transformation."""
        return df
