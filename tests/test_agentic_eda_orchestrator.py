import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

import eazydatafix as edf
from eazydatafix.agentic_eda import AgenticEDAOrchestrator
from eazydatafix.assessment.eda_execution import EDAExecutor
from eazydatafix.assessment.eda_execution.base import EDAAnalysisHandler
from eazydatafix.assessment.eda_execution.registry import default_handlers
from eazydatafix.models.agentic_eda_result import AgenticEDAResult
from eazydatafix.models.eda_plan import EDAPlanStep
from eazydatafix.models.eda_result import EDAResult


def _types(items: list[Any]) -> list[str]:
    return [item.type for item in items]


class _FailingOutlierHandler(EDAAnalysisHandler):
    name = "outlier_analysis"

    def execute(
        self,
        dataframe: pd.DataFrame,
        result: EDAResult,
        step: EDAPlanStep,
    ) -> dict[str, Any]:
        raise RuntimeError("controlled orchestrator test failure")


def test_run_agentic_eda_is_public_and_preserves_version() -> None:
    assert edf.__version__ == "0.3.0"
    assert callable(edf.run_agentic_eda)
    assert "run_agentic_eda" in edf.__all__
    assert edf.AgenticEDAResult is AgenticEDAResult
    assert edf.AgenticEDAConfig is not None


def test_run_agentic_eda_employees_csv_end_to_end() -> None:
    dataset_path = Path(__file__).parents[1] / "employees.csv"

    result = edf.run_agentic_eda(dataset_path)

    assert result.overall_status == "success"
    assert result.eda_result.shape == (5, 8)
    assert result.eda_plan is result.execution_result.eda_plan
    assert result.eda_result is result.execution_result.eda_result
    assert "missing_value_remediation" in _types(result.follow_up_actions)
    assert "identifier_feature_exclusion" in _types(result.follow_up_actions)
    assert "datetime_trend_review" in _types(result.follow_up_actions)
    assert "missing_value_chart" in _types(result.recommended_visualisations)
    assert "time_series_line_chart" in _types(result.recommended_visualisations)
    assert all(item.source_step for item in result.follow_up_actions)


def test_orchestrator_generates_missing_value_decisions() -> None:
    result = edf.run_agentic_eda(
        pd.DataFrame(
            {
                "value": [1.0, 2.0, None, 4.0, 5.0],
                "group": ["A", "A", "B", "B", "B"],
            }
        )
    )

    action = next(
        item for item in result.follow_up_actions if item.type == "missing_value_remediation"
    )
    question = next(
        item for item in result.unresolved_questions if item.type == "missingness_context"
    )

    assert action.target_columns == ["value"]
    assert action.source_step == "missing_value_analysis"
    assert question.target_columns == ["value"]


def test_orchestrator_generates_outlier_and_skewness_decisions() -> None:
    result = edf.run_agentic_eda(pd.DataFrame({"amount": [1, 1, 1, 1, 1, 1, 2, 2, 3, 100]}))

    assert "outlier_review" in _types(result.follow_up_actions)
    assert "skewness_transformation_review" in _types(result.follow_up_actions)
    assert "box_plot" in _types(result.recommended_visualisations)
    assert "histogram" in _types(result.recommended_visualisations)
    assert "outlier_validity" in _types(result.unresolved_questions)


def test_orchestrator_generates_strong_correlation_decisions() -> None:
    result = edf.run_agentic_eda(
        pd.DataFrame(
            {
                "height": list(range(1, 11)),
                "weight": [value * 3 for value in range(1, 11)],
            }
        )
    )

    action = next(
        item for item in result.follow_up_actions if item.type == "multicollinearity_review"
    )

    assert action.target_columns == ["height", "weight"]
    assert action.source_step == "correlation_review"
    assert "correlation_heatmap" in _types(result.recommended_visualisations)


def test_orchestrator_generates_class_imbalance_decisions() -> None:
    result = edf.run_agentic_eda(pd.DataFrame({"target": ["approved"] * 8 + ["rejected"] * 2}))

    assert "class_imbalance_strategy" in _types(result.follow_up_actions)
    assert "class_distribution_chart" in _types(result.recommended_visualisations)
    assert "target_confirmation" in _types(result.unresolved_questions)
    assert "class_imbalance" in _types(result.priority_findings)


def test_orchestrator_generates_datetime_and_boolean_visualisations() -> None:
    result = edf.run_agentic_eda(
        pd.DataFrame(
            {
                "event_date": pd.date_range("2024-01-01", periods=10, freq="D"),
                "is_active": [True] * 7 + [False] * 3,
            }
        )
    )

    visualisation_types = _types(result.recommended_visualisations)

    assert "time_series_line_chart" in visualisation_types
    assert "bar_chart" in visualisation_types
    assert "datetime_semantics" in _types(result.unresolved_questions)


def test_orchestrator_traces_identifier_exclusion() -> None:
    result = edf.run_agentic_eda(
        pd.DataFrame(
            {
                "customer_id": list(range(100, 110)),
                "value": list(range(10)),
            }
        )
    )

    action = next(
        item for item in result.follow_up_actions if item.type == "identifier_feature_exclusion"
    )

    assert action.target_columns == ["customer_id"]
    assert action.source_step == "identifier_exclusion"
    assert "identifier_retention" in _types(result.unresolved_questions)


def test_orchestrator_handles_empty_and_tiny_datasets() -> None:
    empty = edf.run_agentic_eda(pd.DataFrame())
    tiny = edf.run_agentic_eda(pd.DataFrame({"value": [1]}))

    assert empty.overall_status == "success"
    assert empty.execution_result.executed_steps == []
    assert empty.follow_up_actions == []
    assert "No deterministic follow-up actions were generated." in empty.workflow_warnings
    assert tiny.overall_status == "success"
    assert tiny.eda_result.shape == (1, 1)


def test_orchestrator_preserves_partial_execution_failures() -> None:
    handlers = [
        _FailingOutlierHandler() if handler.name == "outlier_analysis" else handler
        for handler in default_handlers()
    ]
    orchestrator = AgenticEDAOrchestrator(executor=EDAExecutor(handlers=handlers))

    result = orchestrator.run(pd.DataFrame({"amount": [1, 2, 2, 3, 100]}))

    assert result.overall_status == "partial_failure"
    assert any("outlier_analysis" in warning for warning in result.workflow_warnings)
    assert "outlier_review" not in _types(result.follow_up_actions)
    assert "skewness_transformation_review" in _types(result.follow_up_actions)


def test_orchestrator_is_deterministic_json_ready_and_non_mutating() -> None:
    dataset = pd.DataFrame(
        {
            "value": [1.0, 2.0, None, 4.0, 100.0],
            "target": ["yes", "yes", "yes", "yes", "no"],
        }
    )
    original = dataset.copy(deep=True)

    first = edf.run_agentic_eda(dataset)
    second = edf.run_agentic_eda(dataset)

    assert first == second
    assert json.loads(json.dumps(first.to_dict())) == first.to_dict()
    pd.testing.assert_frame_equal(dataset, original)


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("correlation_threshold", 0, ValueError),
        ("correlation_threshold", True, TypeError),
        ("outlier_iqr_multiplier", 0, ValueError),
        ("outlier_iqr_multiplier", "wide", TypeError),
        ("class_imbalance_threshold", 1.1, ValueError),
        ("enable_visualisation_recommendations", 1, TypeError),
        ("enable_unresolved_questions", "yes", TypeError),
        ("max_recommendations_per_category", 0, ValueError),
        ("max_recommendations_per_category", 1.5, TypeError),
    ],
)
def test_agentic_eda_config_validation(
    field: str,
    value: object,
    error: type[Exception],
) -> None:
    with pytest.raises(error):
        edf.AgenticEDAConfig(**{field: value})


def test_run_agentic_eda_rejects_non_config_objects() -> None:
    with pytest.raises(
        TypeError,
        match="config must be an AgenticEDAConfig or None",
    ):
        edf.run_agentic_eda(pd.DataFrame(), config={})  # type: ignore[arg-type]


def test_orchestrator_configuration_controls_thresholds() -> None:
    dataset = pd.DataFrame(
        {
            "x": list(range(1, 11)),
            "y": [2, 4, 6, 8, 10, 12, 14, 16, 18, 19],
            "target": ["yes"] * 8 + ["no"] * 2,
        }
    )
    config = edf.AgenticEDAConfig(
        correlation_threshold=1.0,
        outlier_iqr_multiplier=3.0,
        class_imbalance_threshold=0.90,
    )

    result = edf.run_agentic_eda(dataset, config=config)
    successful_outputs = {
        step.name: step.output
        for step in result.execution_result.executed_steps
        if step.status == "success"
    }

    assert successful_outputs["correlation_review"]["threshold"] == 1.0
    assert successful_outputs["outlier_analysis"]["iqr_multiplier"] == 3.0
    assert successful_outputs["class_imbalance_analysis"]["threshold_percentage"] == 90.0
    assert "multicollinearity_review" not in _types(result.follow_up_actions)
    assert "class_imbalance_strategy" not in _types(result.follow_up_actions)


def test_orchestrator_feature_toggles_and_limits() -> None:
    dataset = pd.DataFrame(
        {
            "id": list(range(10)),
            "email": [f"user{index}@example.com" for index in range(10)],
            "value": [1, 1, 1, 1, 1, 1, 2, 2, 3, 100],
        }
    )
    config = edf.AgenticEDAConfig(
        enable_visualisation_recommendations=False,
        enable_unresolved_questions=False,
        max_recommendations_per_category=1,
    )

    result = edf.run_agentic_eda(dataset, config=config)

    assert result.recommended_visualisations == []
    assert result.unresolved_questions == []
    assert len(result.follow_up_actions) == 1
    assert len(result.priority_findings) == 1
