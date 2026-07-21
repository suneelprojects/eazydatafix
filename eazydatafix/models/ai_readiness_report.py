from dataclasses import dataclass

from eazydatafix.models.dataset_profile import DatasetProfile


@dataclass(slots=True)
class AIReadinessReport:
    """
    Represents a dataset's readiness for AI-powered applications.
    """

    overall_score: float
    missing_values_impact: float
    duplicate_records_impact: float
    text_richness: float
    has_unique_identifiers: bool
    structured_column_ratio: float
    unstructured_column_ratio: float
    high_cardinality_columns: list[str]
    low_information_columns: list[str]
    sensitive_columns: list[str]
    metadata_completeness: float
    recommendations: list[str]
    dataset_profile: DatasetProfile
