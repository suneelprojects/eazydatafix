from dataclasses import dataclass


@dataclass(slots=True)
class ValidationResult:
    """
    Represents the outcome of a validation check.
    """

    rule: str
    column: str
    passed: bool
    message: str
