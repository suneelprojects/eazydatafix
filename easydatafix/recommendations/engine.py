from easydatafix.models.recommendation import Recommendation


class RecommendationEngine:
    """
    Generates recommendations based on assessment results.
    """

    def generate(
        self,
        report,
    ) -> list[Recommendation]:

        recommendations: list[Recommendation] = []

        # Completeness

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

        # Uniqueness

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

        # Validity

        invalid_count = sum(
            1
            for validation in report.validations
            if (
                not validation.passed
                and validation.rule
                in {
                    "Email Format",
                    "Phone Number",
                    "Date Format",
                    "URL Format",
                    "IP Address",
                    "Credit Card",
                    "PIN Code",
                    "Aadhaar Number",
                    "PAN Number",
                    "GSTIN",
                }
            )
        )

        if invalid_count > 0:

            recommendations.append(
                Recommendation(
                    title="Fix Invalid Values",
                    description="Some values do not match their expected format.",
                    priority="HIGH",
                    category="Validity",
                    auto_fix_available=False,
                )
            )

        # Consistency

        consistency_count = sum(
            1
            for validation in report.validations
            if (
                not validation.passed
                and validation.rule
                in {
                    "Case Consistency",
                    "Whitespace Consistency",
                    "Duplicate Text",
                }
            )
        )

        if consistency_count > 0:

            recommendations.append(
                Recommendation(
                    title="Improve Data Consistency",
                    description="Standardize text casing, remove extra spaces and resolve inconsistent values.",
                    priority="MEDIUM",
                    category="Consistency",
                    auto_fix_available=True,
                )
            )

        # Accuracy

        accuracy_count = sum(
            1
            for validation in report.validations
            if (
                not validation.passed
                and validation.rule == "Numeric Range"
            )
        )

        if accuracy_count > 0:

            recommendations.append(
                Recommendation(
                    title="Review Numeric Values",
                    description="Some numeric values fall outside the expected range.",
                    priority="HIGH",
                    category="Accuracy",
                    auto_fix_available=False,
                )
            )

        # Timeliness

        timeliness_count = sum(
            1
            for validation in report.validations
            if (
                not validation.passed
                and validation.rule
                in {
                    "Future Date",
                    "Stale Data",
                }
            )
        )

        if timeliness_count > 0:

            recommendations.append(
                Recommendation(
                    title="Review Date Fields",
                    description="Future or stale dates were detected in the dataset.",
                    priority="LOW",
                    category="Timeliness",
                    auto_fix_available=False,
                )
            )

        return recommendations
