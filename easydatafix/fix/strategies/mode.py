from easydatafix.plugins import Plugin
from easydatafix.fix.strategies.base import MissingValueStrategy


class ModeStrategy(Plugin, MissingValueStrategy):
    """
    Fill missing values using mode.
    """

    name = "mode"
    version = "0.2.0"
    author = "EasyDataFix"
    description = "Fill missing values using mode."

    def apply(
        self,
        df,
        applied_fixes: list[str],
    ):

        for column in df.columns:

            if df[column].isna().sum() == 0:
                continue

            mode = df[column].mode()
            value = mode.iloc[0] if not mode.empty else ""

            df[column] = df[column].fillna(value)

            applied_fixes.append(
                f"Filled missing values in '{column}' using mode."
            )

        return df