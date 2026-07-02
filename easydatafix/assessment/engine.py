import pandas as pd

from easydatafix.assessment.checks.completeness import CompletenessCheck
from easydatafix.assessment.checks.uniqueness import UniquenessCheck
from easydatafix.models.assessment_report import AssessmentReport
from easydatafix.core.score_calculator import ScoreCalculator


class AssessmentEngine:
    """
    Coordinates all assessment checks.
    """

    def assess(self, file_path: str) -> AssessmentReport:
        df = pd.read_csv(file_path)

        completeness = CompletenessCheck().evaluate(df)
        uniqueness = UniquenessCheck().evaluate(df)
        
        quality = ScoreCalculator().calculate(
            completeness_score=completeness.completeness_score,
            uniqueness_score=uniqueness.uniqueness_score,
        )

        return AssessmentReport(
            completeness=completeness,
            uniqueness=uniqueness,
            quality=quality,
        )