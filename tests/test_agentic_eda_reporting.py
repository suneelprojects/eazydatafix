import copy
import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

import eazydatafix as edf
from eazydatafix.models.agentic_eda_report_result import AgenticEDAReportResult
from eazydatafix.models.agentic_eda_result import (
    AgenticEDAResult,
    VisualisationRecommendation,
)
from eazydatafix.reporting.agentic_eda import AgenticEDAReportExporter
from eazydatafix.reporting.agentic_eda.charts import (
    ChartContext,
    ChartHandler,
    ChartRegistry,
)
from eazydatafix.reporting.agentic_eda.charts.registry import (
    default_chart_handlers,
)


@pytest.fixture(autouse=True)
def matplotlib_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "matplotlib-cache"))


@pytest.fixture
def employees_path() -> Path:
    return Path(__file__).parents[1] / "employees.csv"


@pytest.fixture
def employees_workflow(
    employees_path: Path,
) -> AgenticEDAResult:
    return edf.run_agentic_eda(employees_path)


class _FailingMissingChartHandler(ChartHandler):
    type = "missing_value_chart"

    def generate(
        self,
        recommendation: VisualisationRecommendation,
        context: ChartContext,
        output_path: Path,
    ) -> None:
        raise RuntimeError("controlled chart failure")


def test_export_agentic_eda_report_is_public() -> None:
    assert edf.__version__ == "0.4.0"
    assert callable(edf.export_agentic_eda_report)
    assert "export_agentic_eda_report" in edf.__all__
    assert edf.AgenticEDAReportResult is AgenticEDAReportResult
    assert edf.AgenticEDAReportExporter is AgenticEDAReportExporter


def test_employees_end_to_end_default_report_generation(
    tmp_path: Path,
    employees_workflow: AgenticEDAResult,
) -> None:
    output_directory = tmp_path / "employees-report"

    result = edf.export_agentic_eda_report(
        employees_workflow,
        output_dir=output_directory,
    )

    assert result.status == "success"
    assert result.output_directory == str(output_directory.resolve())
    assert result.generated_files == [
        "agentic-eda-report.html",
        "agentic-eda-report.json",
    ]
    assert all((output_directory / filename).is_file() for filename in result.generated_files)
    assert [item.type for item in result.generated_visualisations] == [
        "missing_value_chart",
        "bar_chart",
        "time_series_line_chart",
    ]
    assert all((output_directory / item.path).is_file() for item in result.generated_visualisations)


def test_html_report_contains_required_sections_and_relative_images(
    tmp_path: Path,
    employees_workflow: AgenticEDAResult,
) -> None:
    result = edf.export_agentic_eda_report(
        employees_workflow,
        output_dir=tmp_path / "report",
        formats=["html"],
    )
    html = (Path(result.output_directory) / "agentic-eda-report.html").read_text(encoding="utf-8")

    for title in [
        "Report overview",
        "Dataset profile",
        "Semantic column roles",
        "Missing-value analysis",
        "Duplicate review",
        "Numeric distributions",
        "Outlier analysis",
        "Skewness analysis",
        "Categorical distributions",
        "Boolean distributions",
        "Class imbalance",
        "Correlations",
        "Datetime trends",
        "Priority findings",
        "Follow-up actions",
        "Recommended visualisations",
        "Unresolved questions",
        "Workflow warnings",
        "Reproducibility metadata",
    ]:
        assert title in html

    assert 'src="visualisations/' in html
    assert "https://cdn" not in html
    assert "<script" not in html


def test_json_report_contains_workflow_and_artifact_metadata(
    tmp_path: Path,
    employees_workflow: AgenticEDAResult,
) -> None:
    result = edf.export_agentic_eda_report(
        employees_workflow,
        output_dir=tmp_path / "report",
        formats=["json"],
    )
    payload = json.loads(
        (Path(result.output_directory) / "agentic-eda-report.json").read_text(encoding="utf-8")
    )

    assert payload["workflow"] == employees_workflow.to_dict()
    assert payload["report_artifacts"]["output_directory"] == "."
    assert payload["report_artifacts"]["generated_files"] == ["agentic-eda-report.json"]
    assert payload["reproducibility_metadata"]["deterministic"] is True
    assert payload["reproducibility_metadata"]["formats"] == ["json"]


def test_markdown_report_links_generated_charts(
    tmp_path: Path,
    employees_workflow: AgenticEDAResult,
) -> None:
    result = edf.export_agentic_eda_report(
        employees_workflow,
        output_dir=tmp_path / "report",
        formats=["markdown"],
    )
    markdown = (Path(result.output_directory) / "agentic-eda-report.md").read_text(encoding="utf-8")

    assert "# Agentic EDA Report" in markdown
    assert "## Missing-value analysis" in markdown
    assert "![missing_value_chart:" in markdown
    assert "](visualisations/" in markdown


def test_structured_charts_generate_without_raw_dataset(
    tmp_path: Path,
) -> None:
    dataframe = pd.DataFrame(
        {
            "value_a": list(range(10)),
            "value_b": [value * 2 for value in range(10)],
            "department": ["IT"] * 6 + ["Sales"] * 4,
            "is_active": [True] * 7 + [False] * 3,
            "target": ["yes"] * 8 + ["no"] * 2,
            "event_date": pd.date_range("2024-01-01", periods=10, freq="MS"),
        }
    )
    workflow = edf.run_agentic_eda(dataframe)

    result = edf.export_agentic_eda_report(
        workflow,
        output_dir=tmp_path / "report",
        formats=["json"],
    )
    chart_types = [item.type for item in result.generated_visualisations]

    assert "bar_chart" in chart_types
    assert "class_distribution_chart" in chart_types
    assert "correlation_heatmap" in chart_types
    assert "time_series_line_chart" in chart_types
    assert result.skipped_visualisations == []


def test_missing_value_chart_uses_structured_output(
    tmp_path: Path,
) -> None:
    workflow = edf.run_agentic_eda(pd.DataFrame({"amount": [1.0, None, 3.0, 4.0, 5.0]}))

    result = edf.export_agentic_eda_report(
        workflow,
        output_dir=tmp_path / "report",
        formats=["html"],
    )
    chart = next(
        item for item in result.generated_visualisations if item.type == "missing_value_chart"
    )

    assert chart.source_step == "missing_value_analysis"
    assert (Path(result.output_directory) / chart.path).is_file()


def test_raw_data_charts_generate_with_validated_dataset(
    tmp_path: Path,
) -> None:
    dataframe = pd.DataFrame({"amount": [1, 1, 1, 1, 1, 1, 2, 2, 3, 100]})
    workflow = edf.run_agentic_eda(dataframe)

    result = edf.export_agentic_eda_report(
        workflow,
        dataset=dataframe,
        output_dir=tmp_path / "report",
        formats=["json"],
    )
    chart_types = [item.type for item in result.generated_visualisations]

    assert "histogram" in chart_types
    assert "box_plot" in chart_types
    assert not {
        "histogram",
        "box_plot",
    }.intersection(item.type for item in result.skipped_visualisations)


def test_raw_data_charts_are_skipped_honestly_without_dataset(
    tmp_path: Path,
) -> None:
    dataframe = pd.DataFrame({"amount": [1, 1, 1, 1, 1, 1, 2, 2, 3, 100]})
    workflow = edf.run_agentic_eda(dataframe)

    result = edf.export_agentic_eda_report(
        workflow,
        output_dir=tmp_path / "report",
        formats=["json"],
    )
    skipped = {item.type: item.reason for item in result.skipped_visualisations}

    assert "histogram" in skipped
    assert "box_plot" in skipped
    assert "requires the optional validated dataset" in skipped["histogram"]
    assert result.status == "success"


def test_existing_output_directory_is_reused_predictably(
    tmp_path: Path,
    employees_workflow: AgenticEDAResult,
) -> None:
    output_directory = tmp_path / "report"
    output_directory.mkdir()
    unrelated_file = output_directory / "keep.txt"
    unrelated_file.write_text("preserve", encoding="utf-8")

    first = edf.export_agentic_eda_report(
        employees_workflow,
        output_dir=output_directory,
        formats=["html", "json", "markdown"],
    )
    first_html = (output_directory / "agentic-eda-report.html").read_bytes()
    second = edf.export_agentic_eda_report(
        employees_workflow,
        output_dir=output_directory,
        formats=["html", "json", "markdown"],
    )

    assert first == second
    assert (output_directory / "agentic-eda-report.html").read_bytes() == first_html
    assert unrelated_file.read_text(encoding="utf-8") == "preserve"


def test_invalid_output_directories_are_rejected(
    tmp_path: Path,
    employees_workflow: AgenticEDAResult,
) -> None:
    file_path = tmp_path / "not-a-directory"
    file_path.write_text("content", encoding="utf-8")

    with pytest.raises(ValueError, match="not a directory"):
        edf.export_agentic_eda_report(
            employees_workflow,
            output_dir=file_path,
        )

    with pytest.raises(ValueError, match="dedicated report directory"):
        edf.export_agentic_eda_report(
            employees_workflow,
            output_dir=Path.cwd(),
        )


def test_partial_chart_failure_preserves_successful_artifacts(
    tmp_path: Path,
    employees_workflow: AgenticEDAResult,
) -> None:
    handlers = [
        _FailingMissingChartHandler() if handler.type == "missing_value_chart" else handler
        for handler in default_chart_handlers()
    ]
    exporter = AgenticEDAReportExporter(chart_registry=ChartRegistry(handlers=handlers))

    result = exporter.export(
        employees_workflow,
        output_dir=tmp_path / "report",
        formats=["html", "json"],
    )

    assert result.status == "partial_failure"
    assert result.generated_files == [
        "agentic-eda-report.html",
        "agentic-eda-report.json",
    ]
    assert any("controlled chart failure" in warning for warning in result.warnings)
    assert any(
        item.type == "missing_value_chart" and "controlled chart failure" in item.reason
        for item in result.skipped_visualisations
    )
    assert any(item.type == "bar_chart" for item in result.generated_visualisations)


@pytest.mark.parametrize(
    "dataframe",
    [
        pd.DataFrame(),
        pd.DataFrame({"value": [1]}),
    ],
)
def test_empty_and_tiny_workflows_export(
    tmp_path: Path,
    dataframe: pd.DataFrame,
) -> None:
    workflow = edf.run_agentic_eda(dataframe)

    result = edf.export_agentic_eda_report(
        workflow,
        output_dir=tmp_path / f"report-{len(dataframe)}",
    )

    assert result.status == "success"
    assert result.generated_visualisations == []
    assert result.generated_files == [
        "agentic-eda-report.html",
        "agentic-eda-report.json",
    ]


def test_html_escapes_dataset_controlled_values(
    tmp_path: Path,
) -> None:
    unsafe_column = "<script>alert('column')</script>"
    unsafe_value = "<img src=x onerror=alert('value')>"
    workflow = edf.run_agentic_eda(
        pd.DataFrame(
            {
                unsafe_column: [unsafe_value] * 5 + ["safe"] * 5,
            }
        )
    )

    result = edf.export_agentic_eda_report(
        workflow,
        output_dir=tmp_path / "report",
        formats=["html"],
    )
    html = (Path(result.output_directory) / "agentic-eda-report.html").read_text(encoding="utf-8")

    assert unsafe_column not in html
    assert unsafe_value not in html
    assert "&lt;script&gt;" in html
    assert "&lt;img src=x" in html


def test_report_result_is_json_serialisable(
    tmp_path: Path,
    employees_workflow: AgenticEDAResult,
) -> None:
    result = edf.export_agentic_eda_report(
        employees_workflow,
        output_dir=tmp_path / "report",
    )

    assert json.loads(json.dumps(result.to_dict())) == result.to_dict()


def test_export_does_not_mutate_workflow_or_dataframe(
    tmp_path: Path,
) -> None:
    dataframe = pd.DataFrame({"amount": [1, 1, 1, 1, 1, 1, 2, 2, 3, 100]})
    original_dataframe = dataframe.copy(deep=True)
    workflow = edf.run_agentic_eda(dataframe)
    original_workflow = copy.deepcopy(workflow)

    edf.export_agentic_eda_report(
        workflow,
        dataset=dataframe,
        output_dir=tmp_path / "report",
        formats=["html", "json", "markdown"],
    )

    assert workflow == original_workflow
    pd.testing.assert_frame_equal(dataframe, original_dataframe)


def test_supplied_dataset_is_validated_before_output_creation(
    tmp_path: Path,
) -> None:
    dataframe = pd.DataFrame({"amount": [1, 2, 3, 4, 5]})
    workflow = edf.run_agentic_eda(dataframe)
    output_directory = tmp_path / "report"

    with pytest.raises(ValueError, match="shape does not match"):
        edf.export_agentic_eda_report(
            workflow,
            dataset=pd.DataFrame({"amount": [1, 2]}),
            output_dir=output_directory,
        )

    assert not output_directory.exists()


@pytest.mark.parametrize(
    ("formats", "error"),
    [
        ("html", TypeError),
        ([], ValueError),
        (["pdf"], ValueError),
        (["html", 1], TypeError),
    ],
)
def test_report_format_validation(
    tmp_path: Path,
    employees_workflow: AgenticEDAResult,
    formats: Any,
    error: type[Exception],
) -> None:
    with pytest.raises(error):
        edf.export_agentic_eda_report(
            employees_workflow,
            output_dir=tmp_path / "report",
            formats=formats,
        )
