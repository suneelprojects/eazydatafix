import pandas as pd

from eazydatafix.assessment.checks._runner import run_checks
from eazydatafix.models.validation_result import ValidationResult


class FirstCheck:
    def evaluate(
        self,
        df: pd.DataFrame,
    ) -> list[ValidationResult]:
        return [
            ValidationResult(
                rule="First",
                column="value",
                passed=True,
                message="First check ran.",
            )
        ]


class SecondCheck:
    def evaluate(
        self,
        df: pd.DataFrame,
    ) -> list[ValidationResult]:
        return [
            ValidationResult(
                rule="Second",
                column="value",
                passed=True,
                message="Second check ran.",
            )
        ]


def test_run_checks_preserves_check_order() -> None:
    df = pd.DataFrame({"value": [1]})

    results = run_checks(
        [FirstCheck(), SecondCheck()],
        df,
    )

    assert [result.rule for result in results] == [
        "First",
        "Second",
    ]
