from easydatafix.models.assessment_report import AssessmentReport
from easydatafix.models.diagnosis_issue import DiagnosisIssue
from easydatafix.models.diagnosis_report import DiagnosisReport


class DiagnosisEngine:
    """
    Converts an AssessmentReport into a DiagnosisReport.
    """

    def diagnose(
        self,
        report: AssessmentReport,
    ) -> DiagnosisReport:

        diagnosis = DiagnosisReport()

        for recommendation in report.recommendations:

            priority = recommendation.priority.upper()

            if priority not in (
                "HIGH",
                "MEDIUM",
                "LOW",
            ):
                priority = "MEDIUM"

            diagnosis.issues.append(
                DiagnosisIssue(
                    severity=priority,
                    category=recommendation.category,
                    message=recommendation.title,
                    suggestion=recommendation.description,
                    auto_fix_available=(
                        recommendation.auto_fix_available
                    ),
                )
            )

        return diagnosis
