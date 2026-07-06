import pandas as pd

from easydatafix.contracts.fix_step import FixStep
from easydatafix.models.fix_config import FixConfig


class DuplicateRemover(FixStep):
    """
    Removes duplicate rows.
    """

    def run(
        self,
        df: pd.DataFrame,
        config: FixConfig,
        applied_fixes: list[str],
    ) -> pd.DataFrame:

        if not config.remove_duplicates:
            return df

        duplicate_count = int(df.duplicated().sum())

        if duplicate_count > 0:

            df = df.drop_duplicates()

            applied_fixes.append(
                f"Removed {duplicate_count} duplicate row(s)."
            )

        return df
