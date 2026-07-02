from dataclasses import dataclass

from easydatafix.assessment.checks.completeness import CompletenessResult
from easydatafix.assessment.checks.uniqueness import UniquenessResult
from easydatafix.models.quality_score import QualityScore


@dataclass(slots=True)
class AssessmentReport:
    """
    Represents the overall assessment of a dataset.
    """

    completeness: CompletenessResult
    uniqueness: UniquenessResult
    quality: QualityScore
