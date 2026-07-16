import pandas as pd

from easydatafix.plugins import Plugin
from easydatafix.fix.strategies.base import MissingValueStrategy


class SmartStrategy(Plugin, MissingValueStrategy):
    """
    Smart missing value strategy.

    Rules

    Numeric    -> Median
    Boolean    -> Mode
    Category   -> Mode
    Text       -> Keep Missing
    Datetime   -> Keep Missing
    """

    name = "smart"
    version = "1.0.0"
    author = "EasyDataFix"
    description = (
        "Automatically chooses the safest missing "
        "value strategy for each column."
    )

    def apply(
        self,
        df: pd.DataFrame,
        applied_fixes: list[str],
    ) -> pd.DataFrame:

        for column in df.columns:

            series = df[column]

            if series.isna().sum() == 0:
                continue

            # -----------------------------
            # Numeric
            # -----------------------------

            if pd.api.types.is_numeric_dtype(series):

                df[column] = series.fillna(
                    series.median()
                )

                applied_fixes.append(
                    f"Filled numeric column '{column}' using median."
                )

                continue

            # -----------------------------
            # Boolean
            # -----------------------------

            if pd.api.types.is_bool_dtype(series):

                mode = series.mode()

                if not mode.empty:

                    df[column] = series.fillna(
                        mode.iloc[0]
                    )

                    applied_fixes.append(
                        f"Filled boolean column '{column}' using mode."
                    )

                continue

            # -----------------------------
            # Category
            # -----------------------------

            if pd.api.types.is_categorical_dtype(series):

                mode = series.mode()

                if not mode.empty:

                    df[column] = series.fillna(
                        mode.iloc[0]
                    )

                    applied_fixes.append(
                        f"Filled categorical column '{column}' using mode."
                    )

                continue

            # -----------------------------
            # Text & Datetime
            # Leave missing values unchanged.
            # -----------------------------

        return df
