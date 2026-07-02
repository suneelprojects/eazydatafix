from easydatafix.models.quality_score import QualityScore


class ScoreCalculator:
    """
    Calculates the overall data quality score.
    """

    def calculate(
        self,
        completeness_score: float,
        uniqueness_score: float,
    ) -> QualityScore:

        score = round(
            (completeness_score * 0.60)
            + (uniqueness_score * 0.40),
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