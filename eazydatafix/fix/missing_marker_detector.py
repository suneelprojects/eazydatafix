import pandas as pd

from eazydatafix.contracts.fix_step import FixStep
from eazydatafix.models.fix_config import FixConfig


class MissingMarkerDetector(FixStep):
    """Converts configured text missing-value markers to pandas missing values."""

    def run(
        self,
        df: pd.DataFrame,
        config: FixConfig,
        applied_fixes: list[str],
    ) -> pd.DataFrame:
        """Replace exact, case-insensitive markers only in text-like columns."""
        detected = 0
        for column in df.select_dtypes(include=["object", "string"]):
            markers = config.markers_for(column)
            if not markers:
                continue
            normalized_markers = {marker.strip().casefold() for marker in markers}
            values = df[column].astype("string")
            mask = values.str.strip().str.casefold().isin(normalized_markers)
            count = int(mask.sum())
            if count:
                df.loc[mask, column] = pd.NA
                detected += count

        if detected:
            applied_fixes.append(
                f"Converted {detected} configured missing-value marker(s) to missing values."
            )
        return df
