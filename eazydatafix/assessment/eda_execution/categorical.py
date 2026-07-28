from typing import Any

import pandas as pd

from eazydatafix.assessment.eda_execution.base import (
    EDAAnalysisHandler,
    native_value,
    percentage,
)
from eazydatafix.models.eda_plan import EDAPlanStep
from eazydatafix.models.eda_result import EDAResult

_DEFAULT_CLASS_IMBALANCE_THRESHOLD = 80.0
_TOP_CATEGORY_LIMIT = 5


class CategoricalDistributionAnalysisHandler(EDAAnalysisHandler):
    """
    Executes deterministic categorical distribution analysis.
    """

    name = "categorical_distribution_analysis"

    def execute(
        self,
        dataframe: pd.DataFrame,
        result: EDAResult,
        step: EDAPlanStep,
    ) -> dict[str, Any]:
        columns: dict[str, dict[str, Any]] = {}

        for column in step.required_columns:
            series = dataframe[column]
            values = series.dropna()
            value_counts = values.value_counts()
            observed_count = int(values.count())
            frequencies = {
                str(native_value(value)): int(count) for value, count in value_counts.items()
            }
            percentages = {
                str(native_value(value)): percentage(int(count), observed_count)
                for value, count in value_counts.items()
            }
            top_categories = [
                {
                    "value": native_value(value),
                    "count": int(count),
                    "percentage": percentage(int(count), observed_count),
                }
                for value, count in value_counts.iloc[:_TOP_CATEGORY_LIMIT].items()
            ]

            columns[column] = {
                "observed_count": observed_count,
                "missing_count": int(series.isna().sum()),
                "frequency_counts": frequencies,
                "percentages": percentages,
                "top_categories": top_categories,
            }

        return {
            "top_category_limit": _TOP_CATEGORY_LIMIT,
            "columns": columns,
        }


class BooleanDistributionAnalysisHandler(EDAAnalysisHandler):
    """
    Executes deterministic boolean distribution analysis.
    """

    name = "boolean_distribution_analysis"

    def execute(
        self,
        dataframe: pd.DataFrame,
        result: EDAResult,
        step: EDAPlanStep,
    ) -> dict[str, Any]:
        columns: dict[str, dict[str, Any]] = {}

        for column in step.required_columns:
            series = dataframe[column]
            normalized = series.map(self._normalize)
            true_count = int(normalized.eq(True).sum())
            false_count = int(normalized.eq(False).sum())
            valid_count = true_count + false_count
            missing_count = int(series.isna().sum())
            invalid_count = int(len(series) - valid_count - missing_count)

            columns[column] = {
                "true_count": true_count,
                "false_count": false_count,
                "true_percentage": percentage(true_count, valid_count),
                "false_percentage": percentage(false_count, valid_count),
                "missing_count": missing_count,
                "invalid_count": invalid_count,
            }

        return {"columns": columns}

    @staticmethod
    def _normalize(
        value: object,
    ) -> bool | None:
        if value is None or pd.isna(value):
            return None

        if isinstance(value, bool):
            return value

        if isinstance(value, (int, float)) and value in {0, 1}:
            return bool(value)

        normalized = str(value).strip().lower()

        if normalized in {"true", "yes", "1"}:
            return True

        if normalized in {"false", "no", "0"}:
            return False

        return None


class ClassImbalanceAnalysisHandler(EDAAnalysisHandler):
    """
    Executes deterministic class imbalance analysis.
    """

    name = "class_imbalance_analysis"

    def __init__(
        self,
        threshold_percentage: float = _DEFAULT_CLASS_IMBALANCE_THRESHOLD,
    ) -> None:
        """
        Initialise class review with a dominant-class percentage threshold.

        Args:
            threshold_percentage: Inclusive dominance threshold from 0 to 100.
        """
        self._threshold_percentage = threshold_percentage

    def execute(
        self,
        dataframe: pd.DataFrame,
        result: EDAResult,
        step: EDAPlanStep,
    ) -> dict[str, Any]:
        columns: dict[str, dict[str, Any]] = {}

        for column in step.required_columns:
            series = dataframe[column]
            value_counts = series.dropna().value_counts()
            observed_count = int(value_counts.sum())

            if value_counts.empty:
                dominant_class = None
                dominant_count = 0
                dominant_percentage = 0.0
            else:
                dominant_class = native_value(value_counts.index[0])
                dominant_count = int(value_counts.iloc[0])
                dominant_percentage = percentage(dominant_count, observed_count)

            is_imbalanced = dominant_percentage >= self._threshold_percentage
            columns[column] = {
                "dominant_class": dominant_class,
                "dominant_count": dominant_count,
                "dominant_percentage": dominant_percentage,
                "imbalance_status": ("imbalanced" if is_imbalanced else "not_imbalanced"),
                "is_imbalanced": is_imbalanced,
                "missing_count": int(series.isna().sum()),
            }

        return {
            "threshold_percentage": self._threshold_percentage,
            "columns": columns,
        }
