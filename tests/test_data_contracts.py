import pandas as pd

import eazydatafix as edf


def test_schema_inference_and_contract_validation_are_deterministic() -> None:
    """Inferred contracts produce stable explicit pass/fail pipeline reports."""
    dataset = pd.DataFrame({"id": [1, 2], "score": [3.0, 4.0]})
    contract = edf.infer_schema(dataset)
    report = edf.validate_contract(
        dataset,
        contract,
        rules=(edf.QualityRule("score_floor", "score", "min", 0.0),),
    )

    assert report.passed is True
    assert report.to_dict()["passed"] is True
    assert [field.name for field in contract.fields] == ["id", "score"]


def test_contract_reports_missing_extra_and_failed_quality_rules() -> None:
    """Contract failures are explicit rather than raising pipeline-opaque errors."""
    contract = edf.DataContract(
        fields=(edf.SchemaField("id", "int64", nullable=False),),
        allow_extra_columns=False,
    )
    report = edf.validate_contract(
        pd.DataFrame({"id": [1, 1], "extra": ["x", "y"]}),
        contract,
        rules=(edf.QualityRule("unique_id", "id", "unique"),),
    )

    assert report.passed is False
    assert any(result.name == "extra_column" for result in report.results)
    assert any(result.name == "unique_id" and not result.passed for result in report.results)
