import pandas as pd

import eazydatafix as edf


def test_assess_ai_readiness_returns_structured_report() -> None:
    df = pd.DataFrame(
        {
            "record_id": [1, 2, 3],
            "content": ["First document", "Second document", "Third document"],
            "email": [
                "one@example.com",
                "two@example.com",
                "three@example.com",
            ],
            "constant": ["value", "value", "value"],
        }
    )

    report = edf.assess_ai_readiness(df)

    assert 0 <= report.overall_score <= 100
    assert report.missing_values_impact == 100
    assert report.duplicate_records_impact == 100
    assert report.has_unique_identifiers is True
    assert report.text_richness == 50
    assert report.structured_column_ratio == 50
    assert report.unstructured_column_ratio == 50
    assert report.high_cardinality_columns == [
        "record_id",
        "content",
        "email",
    ]
    assert report.low_information_columns == ["constant"]
    assert report.sensitive_columns == ["email"]
    assert report.dataset_profile.rows == 3
    assert any("sensitive" in item.lower() for item in report.recommendations)
