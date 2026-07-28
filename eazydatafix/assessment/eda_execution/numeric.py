from typing import Any

import pandas as pd

from eazydatafix.assessment.eda_execution.base import (
    EDAAnalysisHandler,
    float_or_none,
    native_value,
    percentage,
)
from eazydatafix.models.eda_plan import EDAPlanStep
from eazydatafix.models.eda_result import EDAResult

_DEFAULT_STRONG_CORRELATION_THRESHOLD = 0.80
_DEFAULT_IQR_MULTIPLIER = 1.50


class NumericDistributionAnalysisHandler(EDAAnalysisHandler):
    """
    Executes deterministic numeric distribution analysis.
    """

    name = "numeric_distribution_analysis"

    def execute(
        self,
        dataframe: pd.DataFrame,
        result: EDAResult,
        step: EDAPlanStep,
    ) -> dict[str, Any]:
        columns: dict[str, dict[str, Any]] = {}

        for column in step.required_columns:
            values = pd.to_numeric(dataframe[column], errors="coerce").dropna()

            columns[column] = {
                "count": int(values.count()),
                "missing_count": int(dataframe[column].isna().sum()),
                "mean": float_or_none(values.mean()),
                "median": float_or_none(values.median()),
                "standard_deviation": float_or_none(values.std()),
                "min": float_or_none(values.min()),
                "quartiles": {
                    "25%": float_or_none(values.quantile(0.25)),
                    "50%": float_or_none(values.quantile(0.50)),
                    "75%": float_or_none(values.quantile(0.75)),
                },
                "max": float_or_none(values.max()),
            }

        return {"columns": columns}


class OutlierAnalysisHandler(EDAAnalysisHandler):
    """
    Executes deterministic IQR-based outlier analysis.
    """

    name = "outlier_analysis"

    def __init__(
        self,
        iqr_multiplier: float = _DEFAULT_IQR_MULTIPLIER,
    ) -> None:
        """
        Initialise IQR analysis with a deterministic positive multiplier.

        Args:
            iqr_multiplier: Multiplier applied below Q1 and above Q3.
        """
        self._iqr_multiplier = iqr_multiplier

    def execute(
        self,
        dataframe: pd.DataFrame,
        result: EDAResult,
        step: EDAPlanStep,
    ) -> dict[str, Any]:
        columns: dict[str, dict[str, Any]] = {}

        for column in step.required_columns:
            values = pd.to_numeric(dataframe[column], errors="coerce").dropna()
            q1 = values.quantile(0.25)
            q3 = values.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - self._iqr_multiplier * iqr
            upper_bound = q3 + self._iqr_multiplier * iqr
            outlier_mask = (values < lower_bound) | (values > upper_bound)
            outlier_indices = [native_value(index) for index in values.index[outlier_mask].tolist()]
            outlier_count = int(outlier_mask.sum())

            columns[column] = {
                "method": "IQR",
                "q1": float_or_none(q1),
                "q3": float_or_none(q3),
                "iqr": float_or_none(iqr),
                "lower_bound": float_or_none(lower_bound),
                "upper_bound": float_or_none(upper_bound),
                "outlier_count": outlier_count,
                "outlier_percentage": percentage(outlier_count, len(values)),
                "outlier_row_indices": outlier_indices,
            }

        return {
            "iqr_multiplier": self._iqr_multiplier,
            "columns": columns,
        }


class SkewnessAnalysisHandler(EDAAnalysisHandler):
    """
    Executes deterministic skewness analysis.
    """

    name = "skewness_analysis"

    def execute(
        self,
        dataframe: pd.DataFrame,
        result: EDAResult,
        step: EDAPlanStep,
    ) -> dict[str, Any]:
        columns: dict[str, dict[str, Any]] = {}

        for column in step.required_columns:
            values = pd.to_numeric(dataframe[column], errors="coerce").dropna()

            if len(values) < 3:
                skewness = None
                interpretation = "insufficient_data"
            else:
                skewness = float_or_none(values.skew())
                interpretation = self._interpret(skewness)

            columns[column] = {
                "count": int(values.count()),
                "skewness": skewness,
                "interpretation": interpretation,
                "minimum_required_rows": 3,
            }

        return {"columns": columns}

    @staticmethod
    def _interpret(
        skewness: float | None,
    ) -> str:
        if skewness is None:
            return "insufficient_data"

        absolute_skewness = abs(skewness)

        if absolute_skewness < 0.5:
            return "approximately_symmetric"

        direction = "positive" if skewness > 0 else "negative"

        if absolute_skewness < 1.0:
            return f"moderately_{direction}_skewed"

        return f"highly_{direction}_skewed"


class CorrelationReviewHandler(EDAAnalysisHandler):
    """
    Executes deterministic pairwise correlation review.
    """

    name = "correlation_review"

    def __init__(
        self,
        threshold: float = _DEFAULT_STRONG_CORRELATION_THRESHOLD,
    ) -> None:
        """
        Initialise correlation review with an absolute-correlation threshold.

        Args:
            threshold: Inclusive threshold used to identify strong correlations.
        """
        self._threshold = threshold

    def execute(
        self,
        dataframe: pd.DataFrame,
        result: EDAResult,
        step: EDAPlanStep,
    ) -> dict[str, Any]:
        numeric_frame = dataframe[step.required_columns].apply(
            pd.to_numeric,
            errors="coerce",
        )
        correlation_matrix = numeric_frame.corr()
        matrix = {
            column: {
                related_column: float_or_none(correlation_matrix.loc[column, related_column])
                for related_column in step.required_columns
            }
            for column in step.required_columns
        }
        pairs: list[dict[str, Any]] = []
        strong_pairs: list[dict[str, Any]] = []

        for index, column in enumerate(step.required_columns):
            for related_column in step.required_columns[index + 1 :]:
                correlation = float_or_none(correlation_matrix.loc[column, related_column])
                pair = {
                    "column_a": column,
                    "column_b": related_column,
                    "correlation": correlation,
                }
                pairs.append(pair)

                if correlation is not None and abs(correlation) >= self._threshold:
                    strong_pairs.append(dict(pair))

        return {
            "threshold": self._threshold,
            "matrix": matrix,
            "pairwise_correlations": pairs,
            "strong_correlations": strong_pairs,
        }
