from eazydatafix.validation.engine import ValidationEngine
import pandas as pd


def test_validation_engine(data_dir) -> None:
    df = pd.read_csv(
        data_dir / "validation.csv",
    )

    results = ValidationEngine().validate(df)

    assert len(results) >= 3

    missing_value_results = [
        result
        for result in results
        if result.rule == "Missing Values"
    ]

    assert len(missing_value_results) == len(df.columns)

    email_result = next(
        result
        for result in results
        if result.rule == "Email Format"
    )

    phone_result = next(
        result
        for result in results
        if result.rule == "Phone Number"
    )

    assert not email_result.passed
    assert not phone_result.passed
