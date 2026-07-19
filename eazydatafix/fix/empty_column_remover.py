import pandas as pd

from eazydatafix.contracts.fix_step import FixStep
from eazydatafix.models.fix_config import FixConfig


class EmptyColumnRemover(FixStep):
    """
    Removes completely empty columns.
    """

    def run(
        self,
        df: pd.DataFrame,
        config: FixConfig,
        applied_fixes: list[str],
    ) -> pd.DataFrame:

        if not config.remove_empty_columns:
            return df

        before = len(df.columns)

        df = df.dropna(axis=1, how="all")

        removed = before - len(df.columns)

        if removed > 0:

            applied_fixes.append(
                f"Removed {removed} empty column(s)."
            )

        return df
