from pathlib import Path
from typing import Any

import pandas as pd

from eazydatafix.assessment.checks.uniqueness import UniquenessCheck
from eazydatafix.assessment.profiler import DatasetProfiler
from eazydatafix.core.dataset_loader import DatasetLoader
from eazydatafix.models.dataset_profile import DatasetProfile
from eazydatafix.models.eda_result import EDAResult


class EDAEngine:
    """
    Produces deterministic exploratory data analysis results.
    """

    def analyze(
        self,
        dataset: str | Path | pd.DataFrame,
    ) -> EDAResult:
        """
        Analyze a supported dataset without using an LLM.

        Args:
            dataset: A pandas DataFrame or path to a supported dataset file.

        Returns:
            An EDAResult containing descriptive analysis and recommendations.
        """

        df = DatasetLoader.load(dataset)
        profile = DatasetProfiler().profile(df)
        uniqueness = UniquenessCheck().evaluate(df)

        numeric_source_columns = list(df.select_dtypes(include="number").columns)
        categorical_source_columns = [
            column for column in df.columns if column not in numeric_source_columns
        ]

        numeric_columns = [str(column) for column in numeric_source_columns]
        categorical_columns = [str(column) for column in categorical_source_columns]
        missing_values = {str(column): int(df[column].isna().sum()) for column in df.columns}
        unique_value_counts = {
            str(column): int(df[column].nunique(dropna=True)) for column in df.columns
        }
        numeric_statistics = self._numeric_statistics(
            df,
            numeric_source_columns,
        )
        categorical_summaries = self._categorical_summaries(
            df,
            categorical_source_columns,
        )
        correlation_matrix = self._correlation_matrix(
            df,
            numeric_source_columns,
        )

        observations = self._observations(
            profile=profile,
            missing_values=missing_values,
            duplicate_rows=uniqueness.duplicate_rows,
            numeric_columns=numeric_columns,
            categorical_columns=categorical_columns,
            correlation_matrix=correlation_matrix,
        )
        recommendations = self._recommendations(
            missing_values=missing_values,
            duplicate_rows=uniqueness.duplicate_rows,
            numeric_columns=numeric_columns,
            categorical_columns=categorical_columns,
            unique_value_counts=unique_value_counts,
            row_count=len(df),
        )

        return EDAResult(
            dataset_profile=profile,
            shape=(profile.rows, profile.columns),
            column_names=[str(column) for column in profile.column_names],
            data_types=self._data_types(profile),
            missing_values=missing_values,
            duplicate_rows=uniqueness.duplicate_rows,
            numeric_statistics=numeric_statistics,
            categorical_summaries=categorical_summaries,
            unique_value_counts=unique_value_counts,
            correlation_matrix=correlation_matrix,
            numeric_columns=numeric_columns,
            categorical_columns=categorical_columns,
            observations=observations,
            recommendations=recommendations,
        )

    @staticmethod
    def _data_types(
        profile: DatasetProfile,
    ) -> dict[str, str]:
        return {
            str(column): str(getattr(data_type, "value", data_type))
            for column, data_type in zip(
                profile.column_names,
                profile.data_types,
            )
        }

    @staticmethod
    def _numeric_statistics(
        df: pd.DataFrame,
        numeric_columns: list[object],
    ) -> dict[str, dict[str, float | None]]:
        if not numeric_columns:
            return {}

        statistics = df[numeric_columns].describe().to_dict()

        return {
            str(column): {
                str(statistic): EDAEngine._number_or_none(value)
                for statistic, value in values.items()
            }
            for column, values in statistics.items()
        }

    @staticmethod
    def _categorical_summaries(
        df: pd.DataFrame,
        categorical_columns: list[object],
    ) -> dict[str, dict[str, Any]]:
        summaries: dict[str, dict[str, Any]] = {}

        for column in categorical_columns:
            values = df[column].dropna()
            value_counts = values.value_counts()

            summaries[str(column)] = {
                "count": int(values.count()),
                "missing_count": int(df[column].isna().sum()),
                "unique_count": int(values.nunique()),
                "most_frequent": (
                    None if value_counts.empty else EDAEngine._native_value(value_counts.index[0])
                ),
                "most_frequent_count": (0 if value_counts.empty else int(value_counts.iloc[0])),
            }

        return summaries

    @staticmethod
    def _correlation_matrix(
        df: pd.DataFrame,
        numeric_columns: list[object],
    ) -> dict[str, dict[str, float | None]]:
        if not numeric_columns:
            return {}

        correlations = df[numeric_columns].corr()

        return {
            str(column): {
                str(related_column): EDAEngine._number_or_none(value)
                for related_column, value in values.items()
            }
            for column, values in correlations.to_dict().items()
        }

    @staticmethod
    def _number_or_none(value: object) -> float | None:
        if pd.isna(value):
            return None

        return float(value)

    @staticmethod
    def _native_value(value: object) -> Any:
        item = getattr(value, "item", None)

        if callable(item):
            return item()

        return value

    @staticmethod
    def _observations(
        profile: DatasetProfile,
        missing_values: dict[str, int],
        duplicate_rows: int,
        numeric_columns: list[str],
        categorical_columns: list[str],
        correlation_matrix: dict[str, dict[str, float | None]],
    ) -> list[str]:
        observations = [
            "Dataset contains " f"{profile.rows} row(s) and {profile.columns} column(s).",
            "Detected "
            f"{len(numeric_columns)} numeric and "
            f"{len(categorical_columns)} categorical column(s).",
        ]

        total_missing = sum(missing_values.values())
        observations.append(
            f"Dataset contains {total_missing} missing value(s)."
            if total_missing
            else "Dataset contains no missing values."
        )
        observations.append(
            f"Dataset contains {duplicate_rows} duplicate row(s)."
            if duplicate_rows
            else "Dataset contains no duplicate rows."
        )
        observations.extend(EDAEngine._correlation_observations(correlation_matrix))

        return observations

    @staticmethod
    def _correlation_observations(
        correlation_matrix: dict[str, dict[str, float | None]],
    ) -> list[str]:
        observations: list[str] = []
        inspected_pairs: set[tuple[str, str]] = set()

        for column, correlations in correlation_matrix.items():
            for related_column, correlation in correlations.items():
                pair = tuple(sorted((column, related_column)))

                if column == related_column or pair in inspected_pairs:
                    continue

                inspected_pairs.add(pair)

                if correlation is not None and abs(correlation) >= 0.80:
                    observations.append(
                        "Strong correlation detected between "
                        f"'{column}' and '{related_column}' "
                        f"({correlation:.2f})."
                    )

        return observations

    @staticmethod
    def _recommendations(
        missing_values: dict[str, int],
        duplicate_rows: int,
        numeric_columns: list[str],
        categorical_columns: list[str],
        unique_value_counts: dict[str, int],
        row_count: int,
    ) -> list[str]:
        recommendations: list[str] = []
        missing_columns = [column for column, count in missing_values.items() if count > 0]

        if missing_columns:
            recommendations.append("Review missing values in: " + ", ".join(missing_columns) + ".")

        if duplicate_rows:
            recommendations.append("Remove duplicate rows before downstream analysis.")

        low_information_columns = [
            column for column, unique_count in unique_value_counts.items() if unique_count <= 1
        ]

        if low_information_columns:
            recommendations.append(
                "Review low-information columns: " + ", ".join(low_information_columns) + "."
            )

        high_cardinality_columns = [
            column
            for column in categorical_columns
            if row_count > 0 and unique_value_counts[column] / row_count >= 0.80
        ]

        if high_cardinality_columns:
            recommendations.append(
                "Review high-cardinality categorical columns: "
                + ", ".join(high_cardinality_columns)
                + "."
            )

        if not numeric_columns:
            recommendations.append("Add numeric measures to enable statistical analysis.")

        if not categorical_columns:
            recommendations.append("Add categorical dimensions to support segmentation analysis.")

        if not recommendations:
            recommendations.append("Dataset is ready for further exploratory analysis.")

        return recommendations
