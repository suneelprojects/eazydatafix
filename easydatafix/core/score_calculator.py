from easydatafix.models.quality_score import QualityScore
from easydatafix.models.validation_result import ValidationResult


class ScoreCalculator:
    """
    Calculates the overall data quality score.
    """

    def calculate(
        self,
        completeness_score: float,
        uniqueness_score: float,
        validations: list[ValidationResult] | None = None,
    ) -> QualityScore:

        validity_score = 100.0

        if validations:

            total = len(validations)

            passed = sum(
                1
                for validation in validations
                if validation.passed
            )

            validity_score = round(
                (passed / total) * 100,
                2,
            )

        score = round(
            (
                (completeness_score * 0.35)
                + (uniqueness_score * 0.25)
                + (validity_score * 0.40)
            ),
            2,
        )

        if score >= 95:
            grade = "A+"
        elif score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        else:
            grade = "D"

        return QualityScore(
            score=score,
            grade=grade,
        )
