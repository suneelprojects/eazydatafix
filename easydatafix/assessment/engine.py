import pandas as pd

from easydatafix.assessment.checks.completeness import CompletenessCheck
from easydatafix.assessment.checks.uniqueness import UniquenessCheck
from easydatafix.contracts.check import Check
from easydatafix.core.score_calculator import ScoreCalculator
from easydatafix.models.assessment_report import AssessmentReport
from easydatafix.recommendations.engine import RecommendationEngine
from easydatafix.validation.engine import ValidationEngine


class AssessmentEngine:
    """
    Coordinates all assessment checks.
    """

    def __init__(self) -> None:
        self._checks: list[Check] = [
            CompletenessCheck(),
            UniquenessCheck(),
        ]

    def assess(self, file_path: str) -> AssessmentReport:
        df = pd.read_csv(file_path)

        results = {}

        for check in self._checks:
            results[check.name] = check.evaluate(df)

        completeness = results["Completeness"]
        uniqueness = results["Uniqueness"]

        quality = ScoreCalculator().calculate(
            completeness_score=completeness.completeness_score,
            uniqueness_score=uniqueness.uniqueness_score,
        )

        validations = ValidationEngine().validate(df)

        report = AssessmentReport(
            completeness=completeness,
            uniqueness=uniqueness,
            quality=quality,
            recommendations=[],
            validations=validations,
        )

        report.recommendations = RecommendationEngine().generate(report)

        return report
