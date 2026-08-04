import pandas as pd
import pytest

import eazydatafix as edf
from eazydatafix.models.eda_plan import EDAPlan, EDAPlanStep

_SUPPORTED_STEPS = {
    "missing_value_analysis",
    "duplicate_review",
    "outlier_analysis",
    "numeric_distribution_analysis",
    "skewness_analysis",
    "categorical_distribution_analysis",
    "correlation_review",
    "datetime_trend_analysis",
    "class_imbalance_analysis",
    "identifier_exclusion",
    "boolean_distribution_analysis",
}


def _selected_step(
    plan: EDAPlan,
    name: str,
) -> EDAPlanStep:
    return next(step for step in plan.selected_steps if step.name == name)


def _skipped_step(
    plan: EDAPlan,
    name: str,
) -> EDAPlanStep:
    return next(step for step in plan.skipped_steps if step.name == name)


def test_plan_eda_is_exposed_as_a_public_api() -> None:
    assert edf.__version__ == "0.5.0"
    assert callable(edf.plan_eda)
    assert edf.EDAPlan is EDAPlan
    assert edf.EDAPlanStep is EDAPlanStep
    assert "plan_eda" in edf.__all__


def test_plan_eda_returns_a_complete_structured_plan() -> None:
    result = edf.eda(
        pd.DataFrame(
            {
                "age": [22, 28, 35, 41, 50],
                "salary": [40000, 48000, 61000, 75000, 92000],
                "department": ["Sales", "Sales", "IT", "IT", "IT"],
            }
        )
    )

    plan = edf.plan_eda(result)
    all_steps = plan.selected_steps + plan.skipped_steps

    assert isinstance(plan, EDAPlan)
    assert {step.name for step in all_steps} == _SUPPORTED_STEPS
    assert len(all_steps) == len(_SUPPORTED_STEPS)
    assert all(step.reason for step in all_steps)
    assert all(step.priority for step in all_steps)
    assert all(isinstance(step.required_columns, list) for step in all_steps)
    assert all(isinstance(step.dependencies, list) for step in all_steps)
    assert plan.deterministic_summary.startswith("Selected ")


def test_plan_eda_selects_missing_value_and_duplicate_analysis() -> None:
    result = edf.eda(
        pd.DataFrame(
            {
                "value": [1.0, 1.0, None, 4.0, 5.0],
                "group": ["A", "A", "B", "B", "B"],
            }
        )
    )

    plan = edf.plan_eda(result)

    missing_step = _selected_step(plan, "missing_value_analysis")
    duplicate_step = _selected_step(plan, "duplicate_review")

    assert missing_step.required_columns == ["value"]
    assert missing_step.priority == "high"
    assert duplicate_step.required_columns == ["value", "group"]


def test_plan_eda_skips_missing_value_analysis_when_data_is_complete() -> None:
    result = edf.eda(pd.DataFrame({"value": [1, 2, 3, 4, 5]}))

    plan = edf.plan_eda(result)
    step = _skipped_step(plan, "missing_value_analysis")

    assert step.reason == "No missing values were detected."
    assert step.priority == "not_applicable"


def test_plan_eda_for_numeric_only_data() -> None:
    result = edf.eda(
        pd.DataFrame(
            {
                "age": [20, 25, 30, 35, 40, 45],
                "salary": [35000, 42000, 50000, 61000, 73000, 88000],
            }
        )
    )

    plan = edf.plan_eda(result)

    assert _selected_step(plan, "numeric_distribution_analysis").required_columns == [
        "age",
        "salary",
    ]
    assert _selected_step(plan, "outlier_analysis").dependencies == [
        "numeric_distribution_analysis"
    ]
    assert _selected_step(plan, "skewness_analysis").dependencies == [
        "numeric_distribution_analysis"
    ]
    assert _selected_step(plan, "correlation_review").required_columns == [
        "age",
        "salary",
    ]
    assert _skipped_step(plan, "categorical_distribution_analysis")


def test_plan_eda_for_categorical_only_data() -> None:
    result = edf.eda(
        pd.DataFrame(
            {
                "department": [
                    "Sales",
                    "Sales",
                    "Sales",
                    "IT",
                    "IT",
                    "IT",
                    "IT",
                    "IT",
                ]
            }
        )
    )

    plan = edf.plan_eda(result)

    assert _selected_step(
        plan,
        "categorical_distribution_analysis",
    ).required_columns == ["department"]
    assert _selected_step(plan, "class_imbalance_analysis").required_columns == ["department"]
    assert _skipped_step(plan, "numeric_distribution_analysis")
    assert _skipped_step(plan, "correlation_review")


def test_plan_eda_selects_datetime_trend_analysis() -> None:
    result = edf.eda(
        pd.DataFrame(
            {
                "event_date": [
                    "2024-01-01",
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-04",
                    "2024-01-05",
                ],
                "value": [10, 12, 14, 13, 16],
            }
        )
    )

    plan = edf.plan_eda(result)
    step = _selected_step(plan, "datetime_trend_analysis")

    assert step.required_columns == ["event_date"]
    assert "datetime" in step.reason.lower()


def test_plan_eda_selects_boolean_distribution_analysis() -> None:
    result = edf.eda(
        pd.DataFrame(
            {
                "is_active": [True, True, True, False, True, False],
            }
        )
    )

    plan = edf.plan_eda(result)

    assert _selected_step(plan, "boolean_distribution_analysis").required_columns == ["is_active"]
    assert _selected_step(plan, "class_imbalance_analysis").dependencies == [
        "boolean_distribution_analysis"
    ]


def test_plan_eda_excludes_identifier_heavy_data() -> None:
    result = edf.eda(
        pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5],
                "name": ["Asha", "Ben", "Chen", "Divya", "Eli"],
                "email": [
                    "asha@example.com",
                    "ben@example.com",
                    "chen@example.com",
                    "divya@example.com",
                    "eli@example.com",
                ],
                "phone": [
                    "9000000001",
                    "9000000002",
                    "9000000003",
                    "9000000004",
                    "9000000005",
                ],
            }
        )
    )

    plan = edf.plan_eda(result)
    step = _selected_step(plan, "identifier_exclusion")

    assert step.required_columns == ["id", "name", "email", "phone"]
    assert step.priority == "high"
    assert any("only identifier columns" in warning.lower() for warning in plan.warnings)
    assert _skipped_step(plan, "numeric_distribution_analysis")
    assert _skipped_step(plan, "categorical_distribution_analysis")


def test_plan_eda_prioritizes_observed_class_imbalance() -> None:
    result = edf.eda(
        pd.DataFrame(
            {
                "target": ["approved"] * 9 + ["rejected"],
                "value": list(range(10)),
            }
        )
    )

    plan = edf.plan_eda(result)
    step = _selected_step(plan, "class_imbalance_analysis")

    assert step.required_columns == ["target"]
    assert step.priority == "high"
    assert "dominance" in step.reason.lower()
    assert step.dependencies == ["categorical_distribution_analysis"]


def test_plan_eda_handles_empty_data() -> None:
    result = edf.eda(pd.DataFrame())

    plan = edf.plan_eda(result)

    assert plan.selected_steps == []
    assert len(plan.skipped_steps) == len(_SUPPORTED_STEPS)
    assert any("empty" in warning.lower() for warning in plan.warnings)
    assert "No analysis steps were selected." in plan.deterministic_summary


def test_plan_eda_warns_and_skips_robust_analysis_for_very_small_data() -> None:
    result = edf.eda(pd.DataFrame({"value": [1, 2]}))

    plan = edf.plan_eda(result)

    assert _selected_step(plan, "numeric_distribution_analysis")
    assert _skipped_step(plan, "outlier_analysis")
    assert _skipped_step(plan, "skewness_analysis")
    assert any("only 2 row" in warning.lower() for warning in plan.warnings)


def test_plan_eda_is_deterministic_for_repeated_input() -> None:
    result = edf.eda(
        pd.DataFrame(
            {
                "age": [20, 25, 30, 35, 40],
                "department": ["Sales", "Sales", "IT", "IT", "IT"],
            }
        )
    )

    assert edf.plan_eda(result) == edf.plan_eda(result)


def test_plan_eda_rejects_non_eda_results() -> None:
    with pytest.raises(TypeError, match="expected an EDAResult"):
        edf.plan_eda(pd.DataFrame())
