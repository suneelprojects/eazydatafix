from pathlib import Path

import pandas as pd

from eazydatafix.assessment.checks.completeness import CompletenessCheck
from eazydatafix.assessment.checks.uniqueness import UniquenessCheck
from eazydatafix.assessment.profiler import DatasetProfiler
from eazydatafix.core.column_profiler import ColumnProfiler
from eazydatafix.core.dataset_loader import DatasetLoader
from eazydatafix.enums.data_type import DataType
from eazydatafix.models.ai_readiness_report import AIReadinessReport
from eazydatafix.models.dataset_profile import DatasetProfile


class AIReadinessEngine:
    """
    Assesses whether a dataset is suitable for AI-powered applications.
    """

    SENSITIVE_KEYWORDS = (
        "email",
        "phone",
        "mobile",
        "contact",
        "aadhaar",
        "aadhar",
        "pan",
        "gst",
        "credit",
        "card",
    )

    def assess(
        self,
        dataset: str | Path | pd.DataFrame,
    ) -> AIReadinessReport:
        """
        Assess AI readiness for a supported dataset.

        Args:
            dataset: A pandas DataFrame or path to a supported dataset file.

        Returns:
            An AIReadinessReport with AI suitability metrics and recommendations.
        """

        df = DatasetLoader.load(dataset)
        profile = DatasetProfiler().profile(df)

        completeness = CompletenessCheck().evaluate(df)
        uniqueness = UniquenessCheck().evaluate(df)

        total_columns = len(df.columns)
        semantic_types = {
            str(column): ColumnProfiler.detect(
                str(column),
                df[column],
            )
            for column in df.columns
        }

        text_columns = [
            column
            for column, semantic_type in semantic_types.items()
            if semantic_type == "TEXT"
        ]

        structured_columns = [
            column
            for column, semantic_type in semantic_types.items()
            if semantic_type != "TEXT"
        ]

        identifier_columns = [
            column
            for column, semantic_type in semantic_types.items()
            if semantic_type == "IDENTIFIER"
        ]

        high_cardinality_columns = self._high_cardinality_columns(df)
        low_information_columns = self._low_information_columns(df)
        sensitive_columns = self._sensitive_columns(df)

        text_richness = self._percentage(
            len(text_columns),
            total_columns,
        )

        structured_column_ratio = self._percentage(
            len(structured_columns),
            total_columns,
        )

        unstructured_column_ratio = self._percentage(
            len(text_columns),
            total_columns,
        )

        metadata_completeness = self._metadata_completeness(profile)

        overall_score = self._overall_score(
            completeness_score=completeness.completeness_score,
            uniqueness_score=uniqueness.uniqueness_score,
            text_richness=text_richness,
            has_unique_identifiers=bool(identifier_columns),
            structured_column_ratio=structured_column_ratio,
            metadata_completeness=metadata_completeness,
            high_cardinality_columns=high_cardinality_columns,
            low_information_columns=low_information_columns,
            sensitive_columns=sensitive_columns,
        )

        recommendations = self._recommendations(
            completeness_score=completeness.completeness_score,
            uniqueness_score=uniqueness.uniqueness_score,
            text_columns=text_columns,
            has_unique_identifiers=bool(identifier_columns),
            high_cardinality_columns=high_cardinality_columns,
            low_information_columns=low_information_columns,
            sensitive_columns=sensitive_columns,
            metadata_completeness=metadata_completeness,
        )

        return AIReadinessReport(
            overall_score=overall_score,
            missing_values_impact=completeness.completeness_score,
            duplicate_records_impact=uniqueness.uniqueness_score,
            text_richness=text_richness,
            has_unique_identifiers=bool(identifier_columns),
            structured_column_ratio=structured_column_ratio,
            unstructured_column_ratio=unstructured_column_ratio,
            high_cardinality_columns=high_cardinality_columns,
            low_information_columns=low_information_columns,
            sensitive_columns=sensitive_columns,
            metadata_completeness=metadata_completeness,
            recommendations=recommendations,
            dataset_profile=profile,
        )

    @staticmethod
    def _percentage(
        count: int,
        total: int,
    ) -> float:
        if total == 0:
            return 100.0

        return round((count / total) * 100, 2)

    @staticmethod
    def _high_cardinality_columns(
        df: pd.DataFrame,
    ) -> list[str]:
        high_cardinality_columns: list[str] = []

        for column in df.columns:
            unique_ratio = df[column].nunique(dropna=True) / max(len(df), 1)

            if unique_ratio >= 0.80:
                high_cardinality_columns.append(str(column))

        return high_cardinality_columns

    @staticmethod
    def _low_information_columns(
        df: pd.DataFrame,
    ) -> list[str]:
        return [
            str(column)
            for column in df.columns
            if df[column].nunique(dropna=True) <= 1
        ]

    def _sensitive_columns(
        self,
        df: pd.DataFrame,
    ) -> list[str]:
        return [
            str(column)
            for column in df.columns
            if any(
                keyword in str(column).lower()
                for keyword in self.SENSITIVE_KEYWORDS
            )
        ]

    @staticmethod
    def _metadata_completeness(
        profile: DatasetProfile,
    ) -> float:
        complete_columns = sum(
            1
            for name, data_type in zip(
                profile.column_names,
                profile.data_types,
            )
            if str(name).strip() and data_type != DataType.UNKNOWN
        )

        return AIReadinessEngine._percentage(
            complete_columns,
            profile.columns,
        )

    @staticmethod
    def _overall_score(
        completeness_score: float,
        uniqueness_score: float,
        text_richness: float,
        has_unique_identifiers: bool,
        structured_column_ratio: float,
        metadata_completeness: float,
        high_cardinality_columns: list[str],
        low_information_columns: list[str],
        sensitive_columns: list[str],
    ) -> float:
        score = (
            (completeness_score * 0.30)
            + (uniqueness_score * 0.20)
            + (text_richness * 0.15)
            + ((100.0 if has_unique_identifiers else 0.0) * 0.10)
            + (structured_column_ratio * 0.10)
            + (metadata_completeness * 0.15)
        )

        score -= min(len(high_cardinality_columns) * 2, 10)
        score -= min(len(low_information_columns) * 2, 10)

        if sensitive_columns:
            score -= 5

        return round(max(score, 0.0), 2)

    @staticmethod
    def _recommendations(
        completeness_score: float,
        uniqueness_score: float,
        text_columns: list[str],
        has_unique_identifiers: bool,
        high_cardinality_columns: list[str],
        low_information_columns: list[str],
        sensitive_columns: list[str],
        metadata_completeness: float,
    ) -> list[str]:
        recommendations: list[str] = []

        if completeness_score < 100:
            recommendations.append(
                "Resolve missing values before using the dataset for AI workflows."
            )

        if uniqueness_score < 100:
            recommendations.append(
                "Remove duplicate records to reduce repeated AI context."
            )

        if not text_columns:
            recommendations.append(
                "Add descriptive text fields for RAG, embeddings, or LLM workflows."
            )

        if not has_unique_identifiers:
            recommendations.append(
                "Add a stable unique identifier for traceability and retrieval."
            )

        if high_cardinality_columns:
            recommendations.append(
                "Review high-cardinality columns before embedding or fine-tuning."
            )

        if low_information_columns:
            recommendations.append(
                "Remove or enrich low-information columns before AI use."
            )

        if sensitive_columns:
            recommendations.append(
                "Protect or remove sensitive columns before sending data to AI services."
            )

        if metadata_completeness < 100:
            recommendations.append(
                "Complete column names and data types to improve AI data understanding."
            )

        if not recommendations:
            recommendations.append(
                "Dataset is ready for AI workflows with standard governance controls."
            )

        return recommendations
