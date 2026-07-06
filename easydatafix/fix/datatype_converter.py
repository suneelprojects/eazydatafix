import pandas as pd

from easydatafix.contracts.fix_step import FixStep
from easydatafix.models.fix_config import FixConfig


class DataTypeConverter(FixStep):
    """
    Automatically converts column data types.
    """

    def run(
        self,
        df: pd.DataFrame,
        config: FixConfig,
        applied_fixes: list[str],
    ) -> pd.DataFrame:

        if not config.convert_data_types:
            return df

        converted = []

        for column in df.columns:

            original_dtype = df[column].dtype

            # Try numeric conversion
            try:
                numeric = pd.to_numeric(df[column])

                if numeric.dtype != original_dtype:
                    df[column] = numeric
                    converted.append(column)
                    continue

            except Exception:
                pass

            # Try datetime conversion
            try:
                dt = pd.to_datetime(df[column])

                if dt.dtype != original_dtype:
                    df[column] = dt
                    converted.append(column)

            except Exception:
                pass

        if converted:
            applied_fixes.append(
                "Converted data types: "
                + ", ".join(converted)
            )

        return df
