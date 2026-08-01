import copy
import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

import eazydatafix as edf
from eazydatafix.exceptions import InvalidDatasetError
from eazydatafix.models.agentic_eda_notebook_result import (
    AgenticEDANotebookResult,
)
from eazydatafix.models.agentic_eda_result import AgenticEDAResult
from eazydatafix.reporting.agentic_eda import AgenticEDANotebookExporter


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "employee_id": [101, 102, 103, 104, 105],
            "amount": [10.5, 20.0, None, 40.5, 50.0],
            "department": ["IT", "Sales", "IT", "HR", "Sales"],
            "is_active": [True, True, False, True, False],
            "event_date": pd.date_range("2025-01-01", periods=5, freq="D"),
        }
    )


@pytest.fixture
def sample_workflow(
    sample_dataframe: pd.DataFrame,
) -> AgenticEDAResult:
    return edf.run_agentic_eda(sample_dataframe)


def _read_notebook(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _code_sources(notebook: dict[str, Any]) -> str:
    return "\n".join(cell["source"] for cell in notebook["cells"] if cell["cell_type"] == "code")


def test_notebook_export_is_public() -> None:
    assert callable(edf.export_agentic_eda_notebook)
    assert "export_agentic_eda_notebook" in edf.__all__
    assert edf.AgenticEDANotebookResult is AgenticEDANotebookResult
    assert edf.AgenticEDANotebookExporter is AgenticEDANotebookExporter


@pytest.mark.parametrize("suffix", [".csv", ".xlsx", ".json", ".parquet"])
def test_notebook_export_supports_file_path_datasets(
    tmp_path: Path,
    sample_dataframe: pd.DataFrame,
    suffix: str,
) -> None:
    if suffix == ".parquet":
        pytest.importorskip("pyarrow")

    dataset_path = tmp_path / f"employees{suffix}"

    if suffix == ".csv":
        sample_dataframe.to_csv(dataset_path, index=False)
    elif suffix == ".xlsx":
        sample_dataframe.to_excel(dataset_path, index=False)
    elif suffix == ".json":
        sample_dataframe.to_json(dataset_path, orient="records", date_format="iso")
    else:
        sample_dataframe.to_parquet(dataset_path, index=False)

    workflow = edf.run_agentic_eda(dataset_path)
    output_path = tmp_path / "notebooks" / f"analysis-{suffix[1:]}.ipynb"

    result = edf.export_agentic_eda_notebook(
        workflow,
        dataset=dataset_path,
        output_path=output_path,
    )
    notebook = _read_notebook(output_path)

    assert result.status == "success"
    assert result.notebook_path == str(output_path.resolve())
    assert result.companion_files == []
    assert result.generated_files == [str(output_path.resolve())]
    assert dataset_path.name in _code_sources(notebook)


def test_dataframe_export_creates_deterministic_companion_dataset(
    tmp_path: Path,
    sample_dataframe: pd.DataFrame,
    sample_workflow: AgenticEDAResult,
) -> None:
    output_path = tmp_path / "analysis.ipynb"

    result = edf.export_agentic_eda_notebook(
        sample_workflow,
        dataset=sample_dataframe,
        output_path=output_path,
    )

    assert result.companion_files == [str((tmp_path / "analysis-dataset.json").resolve())]
    companion_path = Path(result.companion_files[0])
    assert companion_path.is_file()
    assert json.loads(companion_path.read_text(encoding="utf-8"))["schema"]["fields"]

    restored = pd.read_json(companion_path, orient="table")
    expected = sample_dataframe.copy()
    expected["event_date"] = expected["event_date"].astype("datetime64[ns]")
    pd.testing.assert_frame_equal(restored, expected)


def test_generated_notebook_has_valid_v4_structure_and_expected_cells(
    tmp_path: Path,
    sample_dataframe: pd.DataFrame,
    sample_workflow: AgenticEDAResult,
) -> None:
    output_path = tmp_path / "analysis.ipynb"
    result = edf.export_agentic_eda_notebook(
        sample_workflow,
        dataset=sample_dataframe,
        output_path=output_path,
    )
    notebook = _read_notebook(output_path)

    assert notebook["nbformat"] == 4
    assert notebook["nbformat_minor"] == 5
    assert result.notebook_format_version == 4
    assert result.cell_count == len(notebook["cells"]) == 23
    assert notebook["metadata"]["kernelspec"]["name"] == "python3"
    assert notebook["metadata"]["eazydatafix"]["deterministic"] is True

    cell_ids = [cell["id"] for cell in notebook["cells"]]
    assert len(cell_ids) == len(set(cell_ids))

    for cell in notebook["cells"]:
        assert cell["metadata"] == {}

        if cell["cell_type"] == "code":
            assert cell["execution_count"] is None
            assert cell["outputs"] == []

    markdown = "\n".join(
        cell["source"] for cell in notebook["cells"] if cell["cell_type"] == "markdown"
    )
    code = _code_sources(notebook)

    for heading in [
        "# Deterministic Agentic EDA Notebook",
        "## Imports",
        "## Dataset loading",
        "## Dataset understanding",
        "## EDA planning",
        "## Plan execution",
        "## Complete Agentic EDA workflow",
        "## Priority findings",
        "## Follow-up actions",
        "## Visualisation recommendations",
        "## Unresolved questions",
        "## Report export",
    ]:
        assert heading in markdown

    for api_call in [
        "edf.eda(dataset)",
        "edf.plan_eda(eda_result)",
        "edf.execute_eda(",
        "edf.run_agentic_eda(dataset, config=config)",
        "workflow.priority_findings",
        "workflow.follow_up_actions",
        "workflow.recommended_visualisations",
        "workflow.unresolved_questions",
        "edf.export_agentic_eda_report(",
    ]:
        assert api_call in code


def test_custom_configuration_is_preserved(
    tmp_path: Path,
    sample_dataframe: pd.DataFrame,
) -> None:
    config = edf.AgenticEDAConfig(
        correlation_threshold=0.91,
        outlier_iqr_multiplier=2.25,
        class_imbalance_threshold=0.72,
        enable_visualisation_recommendations=False,
        enable_unresolved_questions=False,
        max_recommendations_per_category=4,
    )
    workflow = edf.run_agentic_eda(sample_dataframe, config=config)
    output_path = tmp_path / "analysis.ipynb"

    edf.export_agentic_eda_notebook(
        workflow,
        dataset=sample_dataframe,
        output_path=output_path,
        config=config,
    )
    notebook = _read_notebook(output_path)
    code = _code_sources(notebook)

    assert notebook["metadata"]["eazydatafix"]["config"] == {
        "class_imbalance_threshold": 0.72,
        "correlation_threshold": 0.91,
        "enable_unresolved_questions": False,
        "enable_visualisation_recommendations": False,
        "max_recommendations_per_category": 4,
        "outlier_iqr_multiplier": 2.25,
    }
    assert "correlation_threshold=0.91" in code
    assert "outlier_iqr_multiplier=2.25" in code
    assert "enable_visualisation_recommendations=False" in code


def test_dataframe_and_workflow_are_not_mutated(
    tmp_path: Path,
    sample_dataframe: pd.DataFrame,
    sample_workflow: AgenticEDAResult,
) -> None:
    original_dataframe = sample_dataframe.copy(deep=True)
    original_workflow = copy.deepcopy(sample_workflow)

    edf.export_agentic_eda_notebook(
        sample_workflow,
        dataset=sample_dataframe,
        output_path=tmp_path / "analysis.ipynb",
    )

    pd.testing.assert_frame_equal(sample_dataframe, original_dataframe)
    assert sample_workflow == original_workflow


def test_parent_directories_are_created(
    tmp_path: Path,
    sample_dataframe: pd.DataFrame,
    sample_workflow: AgenticEDAResult,
) -> None:
    output_path = tmp_path / "nested" / "notebooks" / "analysis.ipynb"

    result = edf.export_agentic_eda_notebook(
        sample_workflow,
        dataset=sample_dataframe,
        output_path=output_path,
    )

    assert output_path.is_file()
    assert all(Path(path).is_file() for path in result.generated_files)


def test_repeated_exports_are_byte_for_byte_deterministic(
    tmp_path: Path,
    sample_dataframe: pd.DataFrame,
    sample_workflow: AgenticEDAResult,
) -> None:
    output_path = tmp_path / "analysis.ipynb"

    first = edf.export_agentic_eda_notebook(
        sample_workflow,
        dataset=sample_dataframe,
        output_path=output_path,
    )
    first_notebook = output_path.read_bytes()
    companion_path = Path(first.companion_files[0])
    first_companion = companion_path.read_bytes()

    second = edf.export_agentic_eda_notebook(
        sample_workflow,
        dataset=sample_dataframe,
        output_path=output_path,
    )

    assert first == second
    assert output_path.read_bytes() == first_notebook
    assert companion_path.read_bytes() == first_companion


def test_result_is_json_serialisable(
    tmp_path: Path,
    sample_dataframe: pd.DataFrame,
    sample_workflow: AgenticEDAResult,
) -> None:
    result = edf.export_agentic_eda_notebook(
        sample_workflow,
        dataset=sample_dataframe,
        output_path=tmp_path / "analysis.ipynb",
    )

    assert json.loads(json.dumps(result.to_dict())) == result.to_dict()


def test_invalid_arguments_are_rejected_before_writing(
    tmp_path: Path,
    sample_dataframe: pd.DataFrame,
    sample_workflow: AgenticEDAResult,
) -> None:
    output_path = tmp_path / "nested" / "analysis.ipynb"

    with pytest.raises(TypeError, match="workflow must be an AgenticEDAResult"):
        edf.export_agentic_eda_notebook(  # type: ignore[arg-type]
            object(),
            dataset=sample_dataframe,
            output_path=output_path,
        )

    with pytest.raises(TypeError, match="output_path must be"):
        edf.export_agentic_eda_notebook(
            sample_workflow,
            dataset=sample_dataframe,
            output_path=123,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match=r"\.ipynb extension"):
        edf.export_agentic_eda_notebook(
            sample_workflow,
            dataset=sample_dataframe,
            output_path=tmp_path / "analysis.json",
        )

    with pytest.raises(TypeError, match="config must be an AgenticEDAConfig"):
        edf.export_agentic_eda_notebook(
            sample_workflow,
            dataset=sample_dataframe,
            output_path=output_path,
            config={},  # type: ignore[arg-type]
        )

    with pytest.raises(InvalidDatasetError, match="Unsupported dataset type"):
        edf.export_agentic_eda_notebook(
            sample_workflow,
            dataset=123,  # type: ignore[arg-type]
            output_path=output_path,
        )

    assert not output_path.parent.exists()


def test_unsupported_and_mismatched_datasets_are_rejected(
    tmp_path: Path,
    sample_dataframe: pd.DataFrame,
    sample_workflow: AgenticEDAResult,
) -> None:
    unsupported_path = tmp_path / "data.txt"
    unsupported_path.write_text("unsupported", encoding="utf-8")

    with pytest.raises(InvalidDatasetError, match="No data source available"):
        edf.export_agentic_eda_notebook(
            sample_workflow,
            dataset=unsupported_path,
            output_path=tmp_path / "unsupported.ipynb",
        )

    with pytest.raises(ValueError, match="shape does not match"):
        edf.export_agentic_eda_notebook(
            sample_workflow,
            dataset=sample_dataframe.iloc[:2],
            output_path=tmp_path / "mismatched" / "analysis.ipynb",
        )

    assert not (tmp_path / "unsupported.ipynb").exists()
    assert not (tmp_path / "mismatched").exists()


def test_atomic_write_preserves_existing_file_on_replace_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = tmp_path / "analysis.ipynb"
    output_path.write_text("existing notebook", encoding="utf-8")

    def fail_replace(
        source: Path,
        target: Path,
    ) -> Path:
        raise OSError("controlled replace failure")

    monkeypatch.setattr(Path, "replace", fail_replace)

    with pytest.raises(ValueError, match="Unable to write notebook artifact"):
        AgenticEDANotebookExporter._atomic_write_text(
            output_path,
            "replacement notebook",
        )

    assert output_path.read_text(encoding="utf-8") == "existing notebook"
    assert list(tmp_path.glob("*.tmp")) == []


def test_generated_code_cells_execute_without_jupyter(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataframe = pd.DataFrame(
        {
            "value": [1, 2, 3, 4, 5],
            "group": ["A", "A", "B", "B", "B"],
        }
    )
    workflow = edf.run_agentic_eda(dataframe)
    output_path = tmp_path / "analysis.ipynb"
    edf.export_agentic_eda_notebook(
        workflow,
        dataset=dataframe,
        output_path=output_path,
    )
    notebook = _read_notebook(output_path)
    namespace: dict[str, Any] = {}

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "matplotlib-cache"))

    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            exec(
                compile(
                    cell["source"],
                    f"{output_path.name}#{cell['id']}",
                    "exec",
                ),
                namespace,
            )

    assert isinstance(namespace["eda_result"], edf.EDAResult)
    assert isinstance(namespace["workflow"], edf.AgenticEDAResult)
    assert namespace["report"].status == "success"
    assert (tmp_path / "agentic-eda-report" / "agentic-eda-report.json").is_file()
