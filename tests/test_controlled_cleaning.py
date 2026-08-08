import pandas as pd

import eazydatafix as edf


def test_fix_dry_run_detects_missing_markers_without_mutating_input() -> None:
    """Dry-run previews marker normalization and leaves caller data unchanged."""
    dataset = pd.DataFrame(
        {
            " Name ": [" Alice ", "N/A"],
            "score": [10.0, None],
        }
    )
    original = dataset.copy(deep=True)

    result = edf.fix(
        dataset,
        edf.FixConfig(
            missing_value_strategy="mode",
            dry_run=True,
            remove_duplicates=False,
            remove_empty_rows=False,
            remove_empty_columns=False,
        ),
    )

    pd.testing.assert_frame_equal(dataset, original)
    pd.testing.assert_frame_equal(result.dataset, original)
    assert result.proposed_dataset is not None
    assert result.proposed_dataset.loc[1, "name"] == "Alice"
    assert result.dry_run is True
    assert result.change_log
    assert all(change.applied is False for change in result.change_log)
    assert any(change.step == "MissingMarkerDetector" for change in result.change_log)


def test_column_rules_override_global_missing_and_whitespace_settings() -> None:
    """Column rules apply only to the explicitly configured normalized columns."""
    dataset = pd.DataFrame(
        {
            "amount": [10.0, None],
            "label": ["blue", "N/A"],
            "note": [" keep ", " leave "],
        }
    )

    result = edf.fix(
        dataset,
        edf.FixConfig(
            missing_value_strategy="smart",
            remove_duplicates=False,
            remove_empty_rows=False,
            remove_empty_columns=False,
            column_rules={
                "amount": edf.ColumnCleaningRule(missing_value_strategy="mean"),
                "label": edf.ColumnCleaningRule(missing_value_strategy="mode"),
                "note": edf.ColumnCleaningRule(trim_whitespace=False),
            },
        ),
    )

    assert result.dataset.loc[1, "amount"] == 10.0
    assert result.dataset.loc[1, "label"] == "blue"
    assert result.dataset.loc[0, "note"] == " keep "
    assert any(change.step == "missing_values:mean" for change in result.change_log or [])
    assert any(change.step == "missing_values:mode" for change in result.change_log or [])


def test_run_composes_profile_assessment_fix_and_eda() -> None:
    """The unified workflow returns each existing deterministic stage result."""
    dataset = pd.DataFrame({"value": [1, 2, 2], "group": ["a", "a", "b"]})

    result = edf.run(
        dataset,
        edf.FixConfig(
            remove_duplicates=False,
            remove_empty_rows=False,
            remove_empty_columns=False,
        ),
    )

    assert result.profile.rows == 3
    assert result.assessment.quality.score >= 0
    assert result.fix_result.dataset.shape == (3, 2)
    assert result.eda_result.shape == (3, 2)
