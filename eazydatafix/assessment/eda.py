from pathlib import Path
from typing import Any

import pandas as pd

from eazydatafix.assessment.checks.uniqueness import UniquenessCheck
from eazydatafix.assessment.profiler import DatasetProfiler
from eazydatafix.core.dataset_loader import DatasetLoader
from eazydatafix.models.dataset_profile import DatasetProfile
from eazydatafix.models.eda_result import EDAResult

_SEMANTIC_ROLES = (
    "numeric_measure",
    "categorical",
    "identifier",
    "datetime",
    "boolean",
)
_IDENTIFIER_NAME_TOKENS = {
    "code",
    "email",
    "guid",
    "id",
    "mobile",
    "phone",
    "telephone",
    "uuid",
}
_DIGIT_IDENTIFIER_NAME_TOKENS = {
    "account",
    "key",
    "no",
    "number",
    "reference",
    "serial",
}
_DATETIME_NAME_TOKENS = {
    "birth",
    "created",
    "date",
    "datetime",
    "dob",
    "joined",
    "joining",
    "time",
    "timestamp",
    "updated",
}
_BOOLEAN_TRUE_FALSE_VALUES = {"false", "true"}
_BOOLEAN_YES_NO_VALUES = {"no", "yes"}
_DATE_VALUE_PATTERN = (
    r"^(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|" r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4})(?:[ T].*)?$"
)
_HIGH_CARDINALITY_RATIO = 0.80
_MIN_HIGH_CARDINALITY_ROWS = 20
_MIN_HIGH_CARDINALITY_VALUES = 10
_NEAR_UNIQUE_RATIO = 0.95
_MIN_NEAR_UNIQUE_ROWS = 20
_MIN_NEAR_UNIQUE_VALUES = 10


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

        semantic_roles, source_columns_by_role = self._detect_semantic_roles(df)
        numeric_source_columns = source_columns_by_role["numeric_measure"]
        categorical_source_columns = source_columns_by_role["categorical"]
        identifier_source_columns = source_columns_by_role["identifier"]
        datetime_source_columns = source_columns_by_role["datetime"]
        boolean_source_columns = source_columns_by_role["boolean"]

        numeric_columns = [str(column) for column in numeric_source_columns]
        categorical_columns = [str(column) for column in categorical_source_columns]
        identifier_columns = [str(column) for column in identifier_source_columns]
        datetime_columns = [str(column) for column in datetime_source_columns]
        boolean_columns = [str(column) for column in boolean_source_columns]
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
            identifier_columns=identifier_columns,
            datetime_columns=datetime_columns,
            boolean_columns=boolean_columns,
            correlation_matrix=correlation_matrix,
        )
        recommendations = self._recommendations(
            missing_values=missing_values,
            duplicate_rows=uniqueness.duplicate_rows,
            numeric_columns=numeric_columns,
            categorical_columns=categorical_columns,
            identifier_columns=identifier_columns,
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
            semantic_roles=semantic_roles,
            numeric_columns=numeric_columns,
            categorical_columns=categorical_columns,
            identifier_columns=identifier_columns,
            datetime_columns=datetime_columns,
            boolean_columns=boolean_columns,
            observations=observations,
            recommendations=recommendations,
        )

    @staticmethod
    def _detect_semantic_roles(
        df: pd.DataFrame,
    ) -> tuple[dict[str, str], dict[str, list[object]]]:
        semantic_roles: dict[str, str] = {}
        source_columns_by_role: dict[str, list[object]] = {role: [] for role in _SEMANTIC_ROLES}

        for column in df.columns:
            series = df[column]
            role = EDAEngine._semantic_role(column, series)
            semantic_roles[str(column)] = role
            source_columns_by_role[role].append(column)

        return semantic_roles, source_columns_by_role

    @staticmethod
    def _semantic_role(
        column: object,
        series: pd.Series,
    ) -> str:
        if EDAEngine._is_datetime(column, series):
            return "datetime"

        if EDAEngine._is_boolean(column, series):
            return "boolean"

        if EDAEngine._is_identifier(column, series):
            return "identifier"

        if pd.api.types.is_numeric_dtype(series.dtype):
            return "numeric_measure"

        return "categorical"

    @staticmethod
    def _is_datetime(
        column: object,
        series: pd.Series,
    ) -> bool:
        if pd.api.types.is_datetime64_any_dtype(series.dtype):
            return True

        if not (
            pd.api.types.is_object_dtype(series.dtype) or pd.api.types.is_string_dtype(series.dtype)
        ):
            return False

        values = series.dropna().astype("string").str.strip()
        values = values[values.ne("")]

        if values.empty:
            return False

        normalized_name = EDAEngine._normalized_column_name(column)
        name_tokens = set(normalized_name.split("_"))
        has_datetime_name = bool(name_tokens & _DATETIME_NAME_TOKENS)
        date_shaped_ratio = float(values.str.match(_DATE_VALUE_PATTERN).mean())

        if not has_datetime_name and date_shaped_ratio < 0.90:
            return False

        parsed_values = pd.to_datetime(
            values,
            errors="coerce",
            format="mixed",
        )
        required_ratio = 0.80 if has_datetime_name else 0.90

        return float(parsed_values.notna().mean()) >= required_ratio

    @staticmethod
    def _is_boolean(
        column: object,
        series: pd.Series,
    ) -> bool:
        if pd.api.types.is_bool_dtype(series.dtype):
            return True

        values = series.dropna()

        if values.empty:
            return False

        normalized_name = EDAEngine._normalized_column_name(column)
        has_boolean_name = normalized_name.startswith(
            ("is_", "has_", "can_", "should_")
        ) or normalized_name.endswith("_flag")

        if pd.api.types.is_numeric_dtype(series.dtype):
            return has_boolean_name and set(values.unique()).issubset({0, 1})

        normalized_values = {str(value).strip().lower() for value in values.unique()}

        return normalized_values.issubset(_BOOLEAN_TRUE_FALSE_VALUES) or normalized_values.issubset(
            _BOOLEAN_YES_NO_VALUES
        )

    @staticmethod
    def _is_identifier(
        column: object,
        series: pd.Series,
    ) -> bool:
        normalized_name = EDAEngine._normalized_column_name(column)
        name_tokens = set(normalized_name.split("_"))

        if name_tokens & _IDENTIFIER_NAME_TOKENS:
            return True

        values = series.dropna()

        if values.empty:
            return False

        unique_count = int(values.nunique())
        unique_ratio = unique_count / len(values)

        if normalized_name == "name" or normalized_name.endswith("_name"):
            return unique_count >= 2 and unique_ratio >= 0.80

        if name_tokens & _DIGIT_IDENTIFIER_NAME_TOKENS and EDAEngine._values_are_digit_only(values):
            return True

        is_text_like = (
            pd.api.types.is_object_dtype(series.dtype)
            or pd.api.types.is_string_dtype(series.dtype)
            or isinstance(series.dtype, pd.CategoricalDtype)
        )

        return (
            is_text_like
            and len(values) >= _MIN_NEAR_UNIQUE_ROWS
            and unique_count >= _MIN_NEAR_UNIQUE_VALUES
            and unique_ratio >= _NEAR_UNIQUE_RATIO
        )

    @staticmethod
    def _values_are_digit_only(
        values: pd.Series,
    ) -> bool:
        if pd.api.types.is_numeric_dtype(values.dtype):
            numeric_values = pd.to_numeric(values, errors="coerce")
            return bool(numeric_values.notna().all() and (numeric_values % 1 == 0).all())

        normalized_values = values.astype("string").str.strip()
        return bool(normalized_values.str.fullmatch(r"\d+").all())

    @staticmethod
    def _normalized_column_name(
        column: object,
    ) -> str:
        return "_".join(
            part
            for part in "".join(
                character.lower() if character.isalnum() else "_" for character in str(column)
            ).split("_")
            if part
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
        identifier_columns: list[str],
        datetime_columns: list[str],
        boolean_columns: list[str],
        correlation_matrix: dict[str, dict[str, float | None]],
    ) -> list[str]:
        observations = [
            "Dataset contains " f"{profile.rows} row(s) and {profile.columns} column(s).",
            "Detected "
            f"{len(numeric_columns)} numeric measure(s), "
            f"{len(categorical_columns)} categorical, "
            f"{len(identifier_columns)} identifier, "
            f"{len(datetime_columns)} datetime, and "
            f"{len(boolean_columns)} boolean column(s).",
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
        identifier_columns: list[str],
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

        recommendations.extend(
            f"Treat {column} as an identifier rather than a categorical feature."
            for column in identifier_columns
        )

        high_cardinality_columns = [
            column
            for column in categorical_columns
            if (
                row_count >= _MIN_HIGH_CARDINALITY_ROWS
                and unique_value_counts[column] >= _MIN_HIGH_CARDINALITY_VALUES
                and (
                    unique_value_counts[column] / max(row_count - missing_values[column], 1)
                    >= _HIGH_CARDINALITY_RATIO
                )
            )
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
