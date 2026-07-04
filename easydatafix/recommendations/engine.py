from easydatafix.models.recommendation import Recommendation


class RecommendationEngine:
    """
    Generates recommendations based on assessment results.
    """

    def generate(self, report) -> list[Recommendation]:
        recommendations: list[Recommendation] = []

        if report.completeness.total_missing_values > 0:
            recommendations.append(
                Recommendation(
                    title="Handle Missing Values",
                    description="Fill or remove missing values before analysis.",
                    priority="HIGH",
                    category="Completeness",
                    auto_fix_available=True,
                )
            )

        if report.uniqueness.duplicate_rows > 0:
            recommendations.append(
                Recommendation(
                    title="Remove Duplicate Rows",
                    description="Duplicate rows were detected in the dataset.",
                    priority="MEDIUM",
                    category="Uniqueness",
                    auto_fix_available=True,
                )
            )

        return recommendations
