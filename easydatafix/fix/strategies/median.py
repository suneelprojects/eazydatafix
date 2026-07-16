import pandas as pd

from easydatafix.plugins import Plugin
from easydatafix.fix.strategies.base import MissingValueStrategy


class MedianStrategy(Plugin, MissingValueStrategy):
    """
    Fill missing values using median for numeric
    columns and mode for categorical columns.
    """

    name = "median"
    version = "0.2.0"
    author = "EasyDataFix"
    description = (
        "Fill missing numeric values using median and "
        "categorical values using mode."
    )

    def apply(
        self,
        df: pd.DataFrame,
        applied_fixes: list[str],
    ) -> pd.DataFrame:

        for column in df.columns:

            if df[column].isna().sum() == 0:
                continue

            if pd.api.types.is_numeric_dtype(df[column]):
                value = df[column].median()
            else:
                mode = df[column].mode()
                value = mode.iloc[0] if not mode.empty else ""

            df[column] = df[column].fillna(value)

            applied_fixes.append(
                f"Filled missing values in '{column}' using median."
            )

        return df