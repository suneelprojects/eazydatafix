import pandas as pd

from easydatafix.contracts.fix_step import FixStep
from easydatafix.models.fix_config import FixConfig


class EmptyRowRemover(FixStep):
    """
    Removes completely empty rows.
    """

    def run(
        self,
        df: pd.DataFrame,
        config: FixConfig,
        applied_fixes: list[str],
    ) -> pd.DataFrame:

        if not config.remove_empty_rows:
            return df

        before = len(df)

        df = df.dropna(how="all")

        removed = before - len(df)

        if removed > 0:
            applied_fixes.append(
                f"Removed {removed} empty row(s)."
            )

        return df
