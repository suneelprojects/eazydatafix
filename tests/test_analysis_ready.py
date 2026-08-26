import pandas as pd
import pytest

import eazydatafix as edf


def _safe_fix_config(**overrides: object) -> edf.FixConfig:
    """Return a deterministic config suitable for focused readiness tests."""
    values = {
        "remove_duplicates": False,
        "remove_empty_rows": False,
        "remove_empty_columns": False,
        **overrides,
    }
    return edf.FixConfig(**values)


def test_analysis_ready_keeps_dataframe_return_contract_and_input_immutable() -> None:
    """The existing convenience API still returns only a prepared DataFrame."""
    dataset = pd.DataFrame(
        {
            " Customer ID ": ["001", "002"],
            "Order Date": ["2026-08-01", "2026-08-02"],
            "Amount": ["₹1,200", "₹2,400"],
        }
    )
    original = dataset.copy(deep=True)

    result = edf.analysis_ready(dataset, _safe_fix_config())

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["customer_id", "order_date", "amount"]
    assert result["customer_id"].tolist() == ["001", "002"]
    assert pd.api.types.is_datetime64_any_dtype(result["order_date"])
    assert pd.api.types.is_numeric_dtype(result["amount"])
    pd.testing.assert_frame_equal(dataset, original)


def test_analysis_ready_report_composes_scores_changes_and_validation() -> None:
    """The detailed workflow exposes evidence from every composed stage."""
    dataset = pd.DataFrame(
        {
            "score": ["10", "20", "30"],
            "active": ["yes", "no", "yes"],
            "email": ["one@example.com", "invalid", "three@example.com"],
        }
    )

    result = edf.analysis_ready_with_report(
        dataset,
        edf.AnalysisReadyConfig(fix_config=_safe_fix_config()),
    )

    assert isinstance(result, edf.AnalysisReadyResult)
    assert pd.api.types.is_numeric_dtype(result.dataset["score"])
    assert pd.api.types.is_bool_dtype(result.dataset["active"])
    assert result.before_score >= 0
    assert result.after_score >= 0
    assert result.improvement == round(result.after_score - result.before_score, 2)
    assert result.changes
    assert result.validations
    assert any(
        issue.code == "invalid_values" and issue.column == "email" for issue in result.issues
    )
    assert result.is_ready is False


def test_analysis_ready_detects_structural_and_category_issues() -> None:
    """Readiness diagnostics identify low-value and inconsistent columns."""
    dataset = pd.DataFrame(
        {
            "constant": ["same"] * 20,
            "sparse_note": ["only value"] + [None] * 19,
            "region": ["North", "north", "South", "South", "North"] * 4,
        }
    )

    result = edf.analysis_ready_with_report(
        dataset,
        edf.AnalysisReadyConfig(
            fix_config=_safe_fix_config(),
            nearly_empty_threshold=0.80,
        ),
    )

    issue_pairs = {(issue.code, issue.column) for issue in result.issues}
    assert ("constant", "constant") in issue_pairs
    assert ("nearly_empty", "sparse_note") in issue_pairs
    assert ("inconsistent_category", "region") in issue_pairs


def test_analysis_ready_can_derive_date_parts_and_flag_outliers() -> None:
    """Date features and non-destructive outlier flags are explicit opt-ins."""
    dataset = pd.DataFrame(
        {
            "row_id": [101, 102, 103, 104],
            "event_date": ["2026-01-01", "2026-02-02", "2026-03-03", "2026-04-04"],
            "value": [1.0, 2.0, 3.0, 100.0],
        }
    )

    result = edf.analysis_ready_with_report(
        dataset,
        edf.AnalysisReadyConfig(
            fix_config=_safe_fix_config(),
            prepare_config=edf.PrepareConfig(
                outlier_action="flag",
                derive_date_parts=("year", "month", "day_of_week"),
            ),
        ),
    )

    assert result.dataset["row_id"].tolist() == ["101", "102", "103", "104"]
    assert result.dataset["value_is_outlier"].tolist() == [False, False, False, True]
    assert result.dataset["event_date_year"].tolist() == [2026, 2026, 2026, 2026]
    assert result.dataset["event_date_month"].tolist() == [1, 2, 3, 4]
    assert result.dataset["event_date_day_of_week"].tolist()[0] == "Thursday"
    assert any("Derived date parts" in change for change in result.changes)
    assert any("Flagged 1 IQR outlier" in change for change in result.changes)


def test_analysis_ready_dry_run_returns_source_and_candidate_separately() -> None:
    """Dry-run keeps caller-visible data unchanged and reports the full proposal."""
    dataset = pd.DataFrame({"score": ["10", "20", "30"]})

    result = edf.analysis_ready_with_report(
        dataset,
        edf.AnalysisReadyConfig(fix_config=_safe_fix_config(dry_run=True)),
    )

    pd.testing.assert_frame_equal(result.dataset, dataset)
    assert result.proposed_dataset is not None
    assert pd.api.types.is_numeric_dtype(result.proposed_dataset["score"])
    assert result.dry_run is True


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("nearly_empty_threshold", 0.0),
        ("nearly_empty_threshold", 1),
        ("minimum_readiness_score", -1.0),
        ("minimum_readiness_score", 101.0),
    ],
)
def test_analysis_ready_config_rejects_invalid_thresholds(name: str, value: object) -> None:
    """Readiness gates require explicit floats within deterministic ranges."""
    with pytest.raises(ValueError):
        edf.AnalysisReadyConfig(**{name: value})


def test_prepare_config_rejects_unknown_date_parts() -> None:
    """Date feature derivation accepts only documented deterministic parts."""
    with pytest.raises(ValueError):
        edf.PrepareConfig(derive_date_parts=("financial_year",))
