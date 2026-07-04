from dataclasses import dataclass
from typing import TYPE_CHECKING

from easydatafix.assessment.checks.completeness import CompletenessResult
from easydatafix.assessment.checks.uniqueness import UniquenessResult
from easydatafix.models.quality_score import QualityScore
from easydatafix.models.recommendation import Recommendation
from easydatafix.models.validation_result import ValidationResult

if TYPE_CHECKING:
    from easydatafix.report import Report


@dataclass(slots=True)
class AssessmentReport:
    """
    Represents the overall assessment of a dataset.
    """

    completeness: CompletenessResult
    uniqueness: UniquenessResult
    quality: QualityScore
    recommendations: list[Recommendation]
    validations: list[ValidationResult]

    def summary(self) -> None:
        from easydatafix.report import Report

        Report(self).summary()
