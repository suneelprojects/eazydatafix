import pandas as pd

import eazydatafix as edf


def test_prepare_with_report_applies_opt_in_feature_readiness_controls() -> None:
    """Preparation reports explain explicit parsing and text-normalization choices."""
    dataset = pd.DataFrame(
        {
            "event_date": ["2024-01-01", "2024-01-02"],
            "amount": ["10", "20"],
            "note": ["  first   note ", "second note"],
        }
    )
    original = dataset.copy(deep=True)

    report = edf.prepare_with_report(
        dataset,
        edf.PrepareConfig(normalize_text=True),
    )

    pd.testing.assert_frame_equal(dataset, original)
    assert pd.api.types.is_datetime64_any_dtype(report.dataset["event_date"])
    assert pd.api.types.is_numeric_dtype(report.dataset["amount"])
    assert report.dataset.loc[0, "note"] == "first note"
    assert report.shape_before == report.shape_after
    assert report.changes


def test_prepare_outlier_controls_are_explicit_and_deterministic() -> None:
    """IQR capping is applied only when configured and is reported."""
    report = edf.prepare_with_report(
        pd.DataFrame({"value": [1.0, 2.0, 3.0, 100.0]}),
        edf.PrepareConfig(outlier_action="cap"),
    )

    assert report.dataset["value"].max() < 100.0
    assert any("Capped" in change for change in report.changes)
