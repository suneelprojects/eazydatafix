from dataclasses import dataclass, field

from eazydatafix.models.diagnosis_issue import DiagnosisIssue


@dataclass(slots=True)
class DiagnosisReport:
    """
    Represents the diagnosis of a dataset.

    A diagnosis focuses on identifying and prioritizing
    issues that should be fixed before analysis or
    machine learning.
    """

    issues: list[DiagnosisIssue] = field(
        default_factory=list
    )

    @property
    def high(self) -> list[DiagnosisIssue]:
        return [
            issue
            for issue in self.issues
            if issue.severity.upper() == "HIGH"
        ]

    @property
    def medium(self) -> list[DiagnosisIssue]:
        return [
            issue
            for issue in self.issues
            if issue.severity.upper() == "MEDIUM"
        ]

    @property
    def low(self) -> list[DiagnosisIssue]:
        return [
            issue
            for issue in self.issues
            if issue.severity.upper() == "LOW"
        ]

    @property
    def total_issues(self) -> int:
        return len(self.issues)

    def summary(self) -> None:
        """
        Display the diagnosis summary.

        Implementation will be added in the next step.
        """
        raise NotImplementedError(
            "Diagnosis summary is not implemented yet."
        )
