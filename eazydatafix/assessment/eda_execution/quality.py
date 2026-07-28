from typing import Any

import pandas as pd

from eazydatafix.assessment.eda_execution.base import (
    EDAAnalysisHandler,
    native_value,
    percentage,
)
from eazydatafix.models.eda_plan import EDAPlanStep
from eazydatafix.models.eda_result import EDAResult


class MissingValueAnalysisHandler(EDAAnalysisHandler):
    """
    Executes deterministic missing-value analysis.
    """

    name = "missing_value_analysis"

    def execute(
        self,
        dataframe: pd.DataFrame,
        result: EDAResult,
        step: EDAPlanStep,
    ) -> dict[str, Any]:
        total_cells = int(dataframe.shape[0] * dataframe.shape[1])
        affected_columns = []

        for column in step.required_columns:
            count = int(dataframe[column].isna().sum())

            if count:
                affected_columns.append(
                    {
                        "column": column,
                        "count": count,
                        "percentage": percentage(count, len(dataframe)),
                    }
                )

        count = sum(item["count"] for item in affected_columns)

        return {
            "count": count,
            "percentage": percentage(count, total_cells),
            "affected_columns": affected_columns,
        }


class DuplicateReviewHandler(EDAAnalysisHandler):
    """
    Executes deterministic duplicate-row review.
    """

    name = "duplicate_review"

    def execute(
        self,
        dataframe: pd.DataFrame,
        result: EDAResult,
        step: EDAPlanStep,
    ) -> dict[str, Any]:
        duplicate_mask = dataframe.duplicated()
        duplicate_indices = [
            native_value(index) for index in dataframe.index[duplicate_mask].tolist()
        ]
        count = int(duplicate_mask.sum())

        return {
            "duplicate_count": count,
            "duplicate_ratio": round(count / len(dataframe), 6) if len(dataframe) else 0.0,
            "duplicate_percentage": percentage(count, len(dataframe)),
            "duplicate_row_indices": duplicate_indices,
        }


class IdentifierExclusionHandler(EDAAnalysisHandler):
    """
    Summarises identifier columns excluded from feature analysis.
    """

    name = "identifier_exclusion"

    def execute(
        self,
        dataframe: pd.DataFrame,
        result: EDAResult,
        step: EDAPlanStep,
    ) -> dict[str, Any]:
        excluded_columns = [
            {
                "column": column,
                "reason": (
                    "The EDA semantic role is identifier, so the column is "
                    "excluded from feature-oriented statistical analysis."
                ),
            }
            for column in step.required_columns
        ]

        return {
            "count": len(excluded_columns),
            "excluded_columns": excluded_columns,
        }
