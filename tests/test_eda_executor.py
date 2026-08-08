import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

import eazydatafix as edf
from eazydatafix.assessment.eda_execution.base import EDAAnalysisHandler
from eazydatafix.models.eda_execution_result import (
    EDAExecutionResult,
    EDAExecutionStepResult,
)
from eazydatafix.models.eda_plan import EDAPlan, EDAPlanStep
from eazydatafix.models.eda_result import EDAResult


@pytest.fixture
def employees_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 9],
            "name": [
                "Asha",
                "Ben",
                "Chen",
                "Divya",
                "Eli",
                "Fatima",
                "Gita",
                "Hari",
                "Ivan",
                "Ivan",
            ],
            "email": [
                "asha@example.com",
                "ben@example.com",
                "chen@example.com",
                "divya@example.com",
                "eli@example.com",
                "fatima@example.com",
                "gita@example.com",
                "hari@example.com",
                "ivan@example.com",
                "ivan@example.com",
            ],
            "phone": [
                "9000000001",
                "9000000002",
                "9000000003",
                "9000000004",
                "9000000005",
                "9000000006",
                None,
                "9000000008",
                "9000000009",
                "9000000009",
            ],
            "age": [22, 25, 29, 33, 37, 41, 46, 51, 58, 58],
            "salary": [
                40000,
                45000,
                50000,
                58000,
                65000,
                72000,
                80000,
                90000,
                105000,
                105000,
            ],
            "department": [
                "Engineering",
                "Engineering",
                "Engineering",
                "Engineering",
                "Engineering",
                "Engineering",
                "Sales",
                "Sales",
                "HR",
                "HR",
            ],
            "joining_date": [
                "2020-01-15",
                "2020-05-01",
                "2021-02-10",
                "2021-08-20",
                "2022-01-05",
                "2022-07-14",
                "2023-03-03",
                "2023-09-18",
                "2024-04-01",
                "2024-04-01",
            ],
            "is_active": [True, True, True, True, True, True, False, True, False, False],
            "target": [
                "approved",
                "approved",
                "approved",
                "approved",
                "approved",
                "approved",
                "approved",
                "approved",
                "rejected",
                "rejected",
            ],
        }
    )


def _step(
    execution: EDAExecutionResult,
    name: str,
) -> EDAExecutionStepResult:
    return next(step for step in execution.executed_steps if step.name == name)


def _output(
    execution: EDAExecutionResult,
    name: str,
) -> dict[str, Any]:
    step = _step(execution, name)
    assert step.status == "success"
    assert step.output is not None
    return step.output


class _FailingHandler(EDAAnalysisHandler):
    name = "numeric_distribution_analysis"

    def execute(
        self,
        dataframe: pd.DataFrame,
        result: EDAResult,
        step: EDAPlanStep,
    ) -> dict[str, Any]:
        raise RuntimeError("deterministic test failure")


def test_execute_eda_is_exposed_as_a_public_api() -> None:
    assert edf.__version__ == "1.0.0"
    assert callable(edf.execute_eda)
    assert edf.EDAExecutionResult is EDAExecutionResult
    assert edf.EDAExecutionStepResult is EDAExecutionStepResult
    assert "execute_eda" in edf.__all__


def test_execute_eda_runs_full_employee_plan(
    employees_df: pd.DataFrame,
) -> None:
    execution = edf.execute_eda(employees_df)

    assert execution.status == "success"
    assert len(execution.executed_steps) == 11
    assert execution.skipped_steps == []
    assert all(step.status == "success" for step in execution.executed_steps)
    assert execution.execution_order == [step.name for step in execution.eda_plan.selected_steps]
    assert "Executed 11 of 11 selected step(s) successfully" in (execution.deterministic_summary)


def test_execute_eda_runs_full_employees_csv(
    tmp_path: Path,
    employees_df: pd.DataFrame,
) -> None:
    dataset_path = tmp_path / "employees.csv"
    employees_df.to_csv(dataset_path, index=False)

    execution = edf.execute_eda(dataset_path)

    assert execution.status == "success"
    assert len(execution.executed_steps) == 11
    assert all(step.status == "success" for step in execution.executed_steps)
    assert execution.eda_result.column_names == list(employees_df.columns)


def test_execute_eda_missing_value_output(
    employees_df: pd.DataFrame,
) -> None:
    output = _output(edf.execute_eda(employees_df), "missing_value_analysis")

    assert output["count"] == 1
    assert output["percentage"] == 1.0
    assert output["affected_columns"] == [
        {
            "column": "phone",
            "count": 1,
            "percentage": 10.0,
        }
    ]


def test_execute_eda_duplicate_output(
    employees_df: pd.DataFrame,
) -> None:
    output = _output(edf.execute_eda(employees_df), "duplicate_review")

    assert output["duplicate_count"] == 1
    assert output["duplicate_ratio"] == pytest.approx(0.1)
    assert output["duplicate_percentage"] == 10.0
    assert output["duplicate_row_indices"] == [9]


def test_execute_eda_numeric_distribution_output() -> None:
    execution = edf.execute_eda(pd.DataFrame({"value": [1, 2, 3, 4, 5]}))
    metrics = _output(execution, "numeric_distribution_analysis")["columns"]["value"]

    assert metrics["count"] == 5
    assert metrics["mean"] == 3.0
    assert metrics["median"] == 3.0
    assert metrics["standard_deviation"] == pytest.approx(1.5811388301)
    assert metrics["min"] == 1.0
    assert metrics["quartiles"] == {
        "25%": 2.0,
        "50%": 3.0,
        "75%": 4.0,
    }
    assert metrics["max"] == 5.0


def test_execute_eda_iqr_outlier_output() -> None:
    execution = edf.execute_eda(pd.DataFrame({"value": [1, 2, 2, 3, 100]}))
    metrics = _output(execution, "outlier_analysis")["columns"]["value"]

    assert metrics["method"] == "IQR"
    assert metrics["lower_bound"] == pytest.approx(0.5)
    assert metrics["upper_bound"] == pytest.approx(4.5)
    assert metrics["outlier_count"] == 1
    assert metrics["outlier_percentage"] == 20.0
    assert metrics["outlier_row_indices"] == [4]


def test_execute_eda_skewness_output() -> None:
    execution = edf.execute_eda(pd.DataFrame({"value": [1, 1, 1, 2, 10]}))
    metrics = _output(execution, "skewness_analysis")["columns"]["value"]

    assert metrics["skewness"] is not None
    assert metrics["skewness"] > 1
    assert metrics["interpretation"] == "highly_positive_skewed"
    assert metrics["minimum_required_rows"] == 3


def test_execute_eda_categorical_distribution_output() -> None:
    execution = edf.execute_eda(pd.DataFrame({"department": ["IT", "IT", "Sales", "IT", None]}))
    metrics = _output(execution, "categorical_distribution_analysis")["columns"]["department"]

    assert metrics["frequency_counts"] == {"IT": 3, "Sales": 1}
    assert metrics["percentages"] == {"IT": 75.0, "Sales": 25.0}
    assert metrics["missing_count"] == 1
    assert metrics["top_categories"][0] == {
        "value": "IT",
        "count": 3,
        "percentage": 75.0,
    }


def test_execute_eda_boolean_distribution_output() -> None:
    execution = edf.execute_eda(pd.DataFrame({"is_active": [True, True, True, True, False, None]}))
    metrics = _output(execution, "boolean_distribution_analysis")["columns"]["is_active"]

    assert metrics == {
        "true_count": 4,
        "false_count": 1,
        "true_percentage": 80.0,
        "false_percentage": 20.0,
        "missing_count": 1,
        "invalid_count": 0,
    }


def test_execute_eda_class_imbalance_output() -> None:
    execution = edf.execute_eda(
        pd.DataFrame(
            {
                "target": ["approved"] * 8 + ["rejected"] * 2,
            }
        )
    )
    output = _output(execution, "class_imbalance_analysis")
    metrics = output["columns"]["target"]

    assert output["threshold_percentage"] == 80.0
    assert metrics["dominant_class"] == "approved"
    assert metrics["dominant_percentage"] == 80.0
    assert metrics["imbalance_status"] == "imbalanced"
    assert metrics["is_imbalanced"] is True


def test_execute_eda_correlation_output() -> None:
    execution = edf.execute_eda(
        pd.DataFrame(
            {
                "x": [1, 2, 3, 4, 5],
                "y": [2, 4, 6, 8, 10],
            }
        )
    )
    output = _output(execution, "correlation_review")

    assert output["threshold"] == 0.8
    assert output["pairwise_correlations"] == [
        {
            "column_a": "x",
            "column_b": "y",
            "correlation": pytest.approx(1.0),
        }
    ]
    assert output["strong_correlations"] == output["pairwise_correlations"]


def test_execute_eda_datetime_trend_output() -> None:
    execution = edf.execute_eda(
        pd.DataFrame(
            {
                "event_date": [
                    "2024-01-01",
                    "2024-01-15",
                    "invalid",
                    "2024-02-01",
                    "2025-03-01",
                ]
            }
        )
    )
    metrics = _output(execution, "datetime_trend_analysis")["columns"]["event_date"]

    assert metrics["parsed_valid_count"] == 4
    assert metrics["invalid_count"] == 1
    assert metrics["earliest"].startswith("2024-01-01")
    assert metrics["latest"].startswith("2025-03-01")
    assert metrics["date_range_days"] == 425
    assert metrics["year_frequency"] == {"2024": 3, "2025": 1}
    assert metrics["month_frequency"] == {
        "2024-01": 2,
        "2024-02": 1,
        "2025-03": 1,
    }


def test_execute_eda_identifier_exclusion_output(
    employees_df: pd.DataFrame,
) -> None:
    output = _output(edf.execute_eda(employees_df), "identifier_exclusion")

    assert output["count"] == 4
    assert [item["column"] for item in output["excluded_columns"]] == [
        "id",
        "name",
        "email",
        "phone",
    ]
    assert all(item["reason"] for item in output["excluded_columns"])


def test_execute_eda_handles_empty_dataset() -> None:
    execution = edf.execute_eda(pd.DataFrame())

    assert execution.status == "success"
    assert execution.executed_steps == []
    assert len(execution.skipped_steps) == 11
    assert execution.execution_order == []
    assert any("empty" in warning.lower() for warning in execution.warnings)


def test_execute_eda_handles_tiny_dataset() -> None:
    execution = edf.execute_eda(pd.DataFrame({"value": [1, 2]}))

    assert execution.status == "success"
    assert _step(execution, "numeric_distribution_analysis").status == "success"
    assert any("only 2 row" in warning.lower() for warning in execution.warnings)


def test_execute_eda_records_missing_required_column_failure() -> None:
    dataset = pd.DataFrame({"value": [1, 2, 3, 4, 5]})
    result = edf.eda(dataset)
    plan = EDAPlan(
        selected_steps=[
            EDAPlanStep(
                name="numeric_distribution_analysis",
                reason="Explicit test step.",
                priority="medium",
                required_columns=["missing_column"],
                dependencies=[],
            )
        ],
        skipped_steps=[],
        warnings=[],
        deterministic_summary="Explicit test plan.",
    )

    execution = edf.execute_eda(dataset, result=result, plan=plan)

    assert execution.status == "failure"
    assert execution.executed_steps[0].status == "failure"
    assert "missing_column" in execution.executed_steps[0].error
    assert execution.executed_steps[0].output is None


def test_execute_eda_isolates_safe_handler_failures() -> None:
    dataset = pd.DataFrame({"value": [1, 2, 3, 4, 5]})
    result = edf.eda(dataset)
    plan = EDAPlan(
        selected_steps=[
            EDAPlanStep(
                name="numeric_distribution_analysis",
                reason="Explicit failure test.",
                priority="medium",
                required_columns=["value"],
                dependencies=[],
            )
        ],
        skipped_steps=[],
        warnings=[],
        deterministic_summary="Explicit failure plan.",
    )
    executor = edf.EDAExecutor(handlers=[_FailingHandler()])

    execution = executor.execute(dataset, result=result, plan=plan)

    assert execution.status == "failure"
    assert execution.executed_steps[0].status == "failure"
    assert execution.executed_steps[0].error == ("RuntimeError: deterministic test failure")
    assert any("deterministic test failure" in warning for warning in execution.warnings)


def test_execute_eda_validates_explicit_result_against_dataset() -> None:
    result = edf.eda(pd.DataFrame({"value": [1, 2, 3, 4, 5]}))

    with pytest.raises(ValueError, match="does not match"):
        edf.execute_eda(
            pd.DataFrame({"value": [1, 1, 1, 1, 1]}),
            result=result,
        )


def test_execute_eda_is_deterministic_and_serialisable(
    employees_df: pd.DataFrame,
) -> None:
    first = edf.execute_eda(employees_df)
    second = edf.execute_eda(employees_df)

    assert first == second
    assert json.dumps(first.to_dict(), sort_keys=True)


def test_execute_eda_does_not_mutate_input(
    employees_df: pd.DataFrame,
) -> None:
    original = employees_df.copy(deep=True)

    edf.execute_eda(employees_df)

    pd.testing.assert_frame_equal(employees_df, original)


def test_execute_eda_generates_result_and_plan_automatically() -> None:
    execution = edf.execute_eda(pd.DataFrame({"value": [1, 2, 3, 4, 5]}))

    assert isinstance(execution.eda_result, edf.EDAResult)
    assert isinstance(execution.eda_plan, edf.EDAPlan)


def test_execute_eda_uses_explicit_result_and_plan(
    employees_df: pd.DataFrame,
) -> None:
    result = edf.eda(employees_df)
    plan = edf.plan_eda(result)

    execution = edf.execute_eda(
        employees_df,
        result=result,
        plan=plan,
    )

    assert execution.eda_result is result
    assert execution.eda_plan is plan
