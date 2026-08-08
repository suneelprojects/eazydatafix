from eazydatafix.fix.strategies.base import MissingValueStrategy
from eazydatafix.plugins import Plugin


class DropStrategy(Plugin, MissingValueStrategy):
    """
    Drop rows containing missing values.
    """

    name = "drop"
    version = "0.2.0"
    author = "EazyDataFix"
    description = "Drop rows containing missing values."

    def apply(
        self,
        df,
        applied_fixes: list[str],
        columns: list[str] | None = None,
    ):

        for column in columns or list(df.columns):

            if df[column].isna().sum() == 0:
                continue

            before = len(df)

            df = df.dropna(subset=[column])

            removed = before - len(df)

            if removed > 0:
                applied_fixes.append(f"Dropped {removed} row(s) with missing values in '{column}'.")

        return df
