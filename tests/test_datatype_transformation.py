import pandas as pd
import pytest

import eazydatafix as edf


def _conversion_config(**overrides: object) -> edf.FixConfig:
    """Return a focused config that isolates datatype conversion behavior."""
    values = {
        "missing_value_strategy": "smart",
        "remove_duplicates": False,
        "remove_empty_rows": False,
        "remove_empty_columns": False,
        **overrides,
    }
    return edf.FixConfig(**values)


def _conversion_change(result: edf.FixResult) -> edf.CleaningChange:
    """Return the datatype conversion audit entry from a fix result."""
    for change in result.change_log or []:
        if change.step == "DataTypeConverter":
            return change
    raise AssertionError("No datatype conversion audit entry was recorded.")


def _has_conversion(result: edf.FixResult) -> bool:
    """Return whether the result contains a datatype conversion audit entry."""
    return any(change.step == "DataTypeConverter" for change in result.change_log or [])


def test_fix_converts_analysis_types_and_preserves_ids() -> None:
    """Convert common analysis types without damaging identifier values."""
    dataset = pd.DataFrame(
        {
            "customer_id": ["001", "002", "003"],
            "amount": ["₹1,200.50", "₹2,000.00", "₹750.00"],
            "conversion": ["50%", "25%", "100%"],
            "active": ["Yes", "No", "Yes"],
            "order_date": ["2026-08-01", "2026-08-02", "2026-08-03"],
            "score": ["10", "20", "30"],
        }
    )

    result = edf.fix(dataset, _conversion_config())

    assert result.dataset["customer_id"].tolist() == ["001", "002", "003"]
    assert pd.api.types.is_float_dtype(result.dataset["amount"])
    assert result.dataset["amount"].tolist() == [1200.5, 2000.0, 750.0]
    assert result.dataset["conversion"].tolist() == [0.5, 0.25, 1.0]
    assert pd.api.types.is_bool_dtype(result.dataset["active"])
    assert pd.api.types.is_datetime64_any_dtype(result.dataset["order_date"])
    assert pd.api.types.is_integer_dtype(result.dataset["score"])
    assert _has_conversion(result)
    assert any("currency numeric" in fix for fix in result.applied_fixes)


def test_fix_rejects_numeric_conversion_below_confidence_threshold() -> None:
    """Low-confidence conversion leaves the original values and dtype intact."""
    dataset = pd.DataFrame({"measurement": ["10", "20", "unknown", "not recorded"]})

    result = edf.fix(
        dataset,
        _conversion_config(numeric_conversion_threshold=0.75),
    )

    assert result.dataset["measurement"].tolist() == dataset["measurement"].tolist()
    assert result.dataset["measurement"].dtype == dataset["measurement"].dtype
    assert not _has_conversion(result)


def test_fix_uses_date_threshold_and_audits_new_missing_values() -> None:
    """Accepted partial date parsing exposes invalid values through the audit log."""
    dataset = pd.DataFrame(
        {"order_date": ["2026-08-01", "2026-08-02", "2026-08-03", "invalid"]}
    )

    result = edf.fix(
        dataset,
        _conversion_config(date_parsing_threshold=0.75),
    )

    assert pd.api.types.is_datetime64_any_dtype(result.dataset["order_date"])
    assert pd.isna(result.dataset.loc[3, "order_date"])
    conversion = _conversion_change(result)
    assert conversion.missing_values_before == 0
    assert conversion.missing_values_after == 1


def test_fix_can_disable_datatype_conversion() -> None:
    """The existing convert_data_types switch remains authoritative."""
    dataset = pd.DataFrame({"score": ["10", "20", "30"]})

    result = edf.fix(dataset, _conversion_config(convert_data_types=False))

    pd.testing.assert_frame_equal(result.dataset, dataset)
    assert not _has_conversion(result)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("numeric_conversion_threshold", 0.0),
        ("numeric_conversion_threshold", 1),
        ("date_parsing_threshold", 1.1),
        ("date_parsing_threshold", "0.8"),
    ],
)
def test_config_rejects_invalid_thresholds(name: str, value: object) -> None:
    """Confidence thresholds must be explicit floats within the supported range."""
    with pytest.raises(ValueError):
        edf.FixConfig(**{name: value})


def test_fix_dry_run_previews_datatype_conversion_without_mutating_input() -> None:
    """Dry-run keeps the caller data while exposing the fully converted proposal."""
    dataset = pd.DataFrame({"score": ["10", "20", "30"]})
    original = dataset.copy(deep=True)

    result = edf.fix(dataset, _conversion_config(dry_run=True))

    pd.testing.assert_frame_equal(dataset, original)
    pd.testing.assert_frame_equal(result.dataset, original)
    assert result.proposed_dataset is not None
    assert pd.api.types.is_integer_dtype(result.proposed_dataset["score"])
    conversion = _conversion_change(result)
    assert conversion.applied is False
