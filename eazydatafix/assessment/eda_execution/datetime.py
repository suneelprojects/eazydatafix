from typing import Any

import pandas as pd

from eazydatafix.assessment.eda_execution.base import (
    EDAAnalysisHandler,
    native_value,
)
from eazydatafix.models.eda_plan import EDAPlanStep
from eazydatafix.models.eda_result import EDAResult


class DatetimeTrendAnalysisHandler(EDAAnalysisHandler):
    """
    Executes deterministic datetime range and frequency analysis.
    """

    name = "datetime_trend_analysis"

    def execute(
        self,
        dataframe: pd.DataFrame,
        result: EDAResult,
        step: EDAPlanStep,
    ) -> dict[str, Any]:
        columns: dict[str, dict[str, Any]] = {}

        for column in step.required_columns:
            series = dataframe[column]
            parsed = pd.to_datetime(
                series,
                errors="coerce",
                format="mixed",
            )
            valid = parsed.dropna()
            missing_count = int(series.isna().sum())
            invalid_count = int(series.notna().sum() - valid.count())

            if valid.empty:
                earliest = None
                latest = None
                date_range = None
                date_range_days = None
                year_frequency: dict[str, int] = {}
                month_frequency: dict[str, int] = {}
            else:
                earliest_value = valid.min()
                latest_value = valid.max()
                earliest = native_value(earliest_value)
                latest = native_value(latest_value)
                date_range_value = latest_value - earliest_value
                date_range = str(date_range_value)
                date_range_days = int(date_range_value.days)
                year_counts = valid.dt.year.value_counts().sort_index()
                month_counts = valid.dt.to_period("M").astype(str).value_counts().sort_index()
                year_frequency = {str(year): int(count) for year, count in year_counts.items()}
                month_frequency = {str(month): int(count) for month, count in month_counts.items()}

            columns[column] = {
                "parsed_valid_count": int(valid.count()),
                "invalid_count": invalid_count,
                "missing_count": missing_count,
                "earliest": earliest,
                "latest": latest,
                "date_range": date_range,
                "date_range_days": date_range_days,
                "year_frequency": year_frequency,
                "month_frequency": month_frequency,
            }

        return {"columns": columns}
