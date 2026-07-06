import pandas as pd

from easydatafix.contracts.fix_step import FixStep
from easydatafix.models.fix_config import FixConfig


class WhitespaceTrimmer(FixStep):
    """
    Trims leading and trailing whitespace
    from string columns.
    """

    def run(
        self,
        df: pd.DataFrame,
        config: FixConfig,
        applied_fixes: list[str],
    ) -> pd.DataFrame:

        if not config.trim_whitespace:
            return df

        before = df.copy()

        for column in df.select_dtypes(include=["object", "string"]):
            df[column] = df[column].astype(str).str.strip()

        if not before.equals(df):
            applied_fixes.append(
                "Trimmed leading/trailing whitespaces."
            )

        return df
