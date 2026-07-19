import re

import pandas as pd

from eazydatafix.contracts.fix_step import FixStep
from eazydatafix.models.fix_config import FixConfig


class ColumnNormalizer(FixStep):
    """
    Normalizes column names.
    """

    def run(
        self,
        df: pd.DataFrame,
        config: FixConfig,
        applied_fixes: list[str],
    ) -> pd.DataFrame:

        if not config.normalize_column_names:
            return df

        original_columns = list(df.columns)

        columns = []

        for column in df.columns:

            name = str(column).strip().lower()

            name = re.sub(r"[^\w]+", "_", name)

            name = re.sub(r"_+", "_", name)

            name = name.strip("_")

            columns.append(name)

        df.columns = columns

        if original_columns != list(df.columns):
            applied_fixes.append(
                "Normalized column names."
            )

        return df
