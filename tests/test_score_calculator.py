from eazydatafix.core.score_calculator import ScoreCalculator
from eazydatafix.models.validation_result import ValidationResult


def test_score_calculator_perfect() -> None:
    calculator = ScoreCalculator()

    quality = calculator.calculate(
        completeness_score=100,
        uniqueness_score=100,
    )

    assert quality.score == 100
    assert quality.grade == "A+"


def test_score_calculator_without_validations() -> None:
    calculator = ScoreCalculator()

    quality = calculator.calculate(
        completeness_score=80,
        uniqueness_score=90,
    )

    assert quality.score == 90.5
    assert quality.grade == "A"


def test_score_calculator_with_failed_validations() -> None:
    calculator = ScoreCalculator()

    validations = [
        ValidationResult(
            rule="Email",
            column="email",
            passed=True,
            message="OK",
        ),
        ValidationResult(
            rule="Phone",
            column="phone",
            passed=False,
            message="Invalid",
        ),
    ]

    quality = calculator.calculate(
        completeness_score=100,
        uniqueness_score=100,
        validations=validations,
    )

    assert quality.score == 80.0
    assert quality.grade == "B"
