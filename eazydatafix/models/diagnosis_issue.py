from dataclasses import dataclass


@dataclass(slots=True)
class DiagnosisIssue:
    """
    Represents a single issue detected in a dataset.
    """

    severity: str
    category: str
    message: str
    suggestion: str
    auto_fix_available: bool = False
