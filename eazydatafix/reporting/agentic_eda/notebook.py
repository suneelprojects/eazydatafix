import json
import os
from dataclasses import asdict
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import pandas as pd

from eazydatafix.assessment.eda_validation import (
    load_eda_frame,
    validate_eda_result,
)
from eazydatafix.models.agentic_eda_config import AgenticEDAConfig
from eazydatafix.models.agentic_eda_notebook_result import (
    AgenticEDANotebookResult,
)
from eazydatafix.models.agentic_eda_result import AgenticEDAResult

_NOTEBOOK_FORMAT_VERSION = 4
_NOTEBOOK_FORMAT_MINOR_VERSION = 5


class AgenticEDANotebookExporter:
    """Exports deterministic, ready-to-run Agentic EDA Jupyter notebooks."""

    def export(
        self,
        workflow: AgenticEDAResult,
        dataset: str | Path | pd.DataFrame,
        output_path: str | Path = "agentic-eda.ipynb",
        config: AgenticEDAConfig | None = None,
    ) -> AgenticEDANotebookResult:
        """
        Export an unexecuted notebook that reproduces an Agentic EDA workflow.

        Args:
            workflow: Existing result returned by ``run_agentic_eda``.
            dataset: Matching DataFrame or supported dataset file path.
            output_path: Destination ``.ipynb`` file.
            config: Configuration used to reproduce the complete workflow.

        Returns:
            Structured notebook artifact metadata.

        Raises:
            TypeError: If workflow, output_path, or config has an invalid type.
            ValueError: If output_path or the supplied dataset is invalid.
        """
        if not isinstance(workflow, AgenticEDAResult):
            raise TypeError("export_agentic_eda_notebook() workflow must be an AgenticEDAResult.")

        notebook_path = self._normalise_output_path(output_path)
        selected_config = self._validate_config(config)
        dataframe = load_eda_frame(dataset)
        validate_eda_result(dataframe, workflow.eda_result)
        companion_path, companion_content = self._companion_artifact(
            dataset=dataset,
            dataframe=dataframe,
            notebook_path=notebook_path,
        )
        notebook = self._notebook(
            workflow=workflow,
            dataset=dataset,
            notebook_path=notebook_path,
            companion_path=companion_path,
            config=selected_config,
            config_was_supplied=config is not None,
        )
        notebook_content = (
            json.dumps(
                notebook,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            + "\n"
        )

        self._prepare_parent_directory(notebook_path)

        if companion_path is not None and companion_content is not None:
            self._atomic_write_text(companion_path, companion_content)

        self._atomic_write_text(notebook_path, notebook_content)

        companion_files = [str(companion_path)] if companion_path is not None else []
        generated_files = [str(notebook_path), *companion_files]

        return AgenticEDANotebookResult(
            notebook_path=str(notebook_path),
            generated_files=generated_files,
            companion_files=companion_files,
            cell_count=len(notebook["cells"]),
            notebook_format_version=_NOTEBOOK_FORMAT_VERSION,
            deterministic_summary=(
                f"Generated a deterministic Agentic EDA notebook with "
                f"{len(notebook['cells'])} cell(s) and "
                f"{len(companion_files)} companion file(s)."
            ),
            status="success",
        )

    @staticmethod
    def _normalise_output_path(
        output_path: str | Path,
    ) -> Path:
        if not isinstance(output_path, (str, Path)):
            raise TypeError("output_path must be a string or pathlib.Path.")

        if isinstance(output_path, str) and not output_path.strip():
            raise ValueError("output_path must identify a .ipynb file.")

        notebook_path = Path(output_path).expanduser().resolve()

        if notebook_path.suffix.lower() != ".ipynb":
            raise ValueError("output_path must use the .ipynb extension.")

        if notebook_path.exists() and not notebook_path.is_file():
            raise ValueError(f"Notebook output path is not a file: {notebook_path}")

        return notebook_path

    @staticmethod
    def _validate_config(
        config: AgenticEDAConfig | None,
    ) -> AgenticEDAConfig:
        if config is None:
            return AgenticEDAConfig()

        if not isinstance(config, AgenticEDAConfig):
            raise TypeError(
                "export_agentic_eda_notebook() config must be an AgenticEDAConfig or None."
            )

        return config

    @staticmethod
    def _companion_artifact(
        dataset: str | Path | pd.DataFrame,
        dataframe: pd.DataFrame,
        notebook_path: Path,
    ) -> tuple[Path | None, str | None]:
        if not isinstance(dataset, pd.DataFrame):
            return None, None

        companion_path = notebook_path.with_name(f"{notebook_path.stem}-dataset.json")
        pandas_json = dataframe.to_json(
            orient="table",
            date_format="iso",
            date_unit="ns",
            double_precision=15,
            force_ascii=False,
            index=False,
        )
        payload = json.loads(pandas_json)
        content = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        return companion_path, content

    @staticmethod
    def _prepare_parent_directory(
        notebook_path: Path,
    ) -> None:
        parent = notebook_path.parent

        if parent.exists() and not parent.is_dir():
            raise ValueError(f"Notebook parent path is not a directory: {parent}")

        try:
            parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ValueError(f"Unable to create notebook output directory: {parent}") from exc

    @staticmethod
    def _atomic_write_text(
        path: Path,
        content: str,
    ) -> None:
        temporary_path: Path | None = None

        try:
            with NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_file.write(content)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
                temporary_path = Path(temporary_file.name)

            temporary_path.replace(path)
        except OSError as exc:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

            raise ValueError(f"Unable to write notebook artifact: {path}") from exc

    def _notebook(
        self,
        workflow: AgenticEDAResult,
        dataset: str | Path | pd.DataFrame,
        notebook_path: Path,
        companion_path: Path | None,
        config: AgenticEDAConfig,
        config_was_supplied: bool,
    ) -> dict[str, Any]:
        cells = [
            self._markdown_cell(
                "workflow-overview",
                "# Deterministic Agentic EDA Notebook\n\n"
                "This notebook reproduces EazyDataFix dataset understanding, "
                "planning, deterministic execution, follow-up decisions, and "
                "report export without requiring an LLM.\n\n"
                "**Workflow:** dataset → understand → plan → execute → decide → report\n",
            ),
            self._markdown_cell(
                "imports-heading",
                "## Imports\n\nImport EazyDataFix and the local data-loading helpers.\n",
            ),
            self._code_cell(
                "imports",
                "from pathlib import Path\n\n"
                "import pandas as pd\n\n"
                "import eazydatafix as edf\n",
            ),
            self._markdown_cell(
                "dataset-heading",
                "## Dataset loading\n\nLoad the source dataset used by the exported workflow.\n",
            ),
            self._code_cell(
                "dataset-loading",
                self._dataset_source(
                    dataset=dataset,
                    notebook_path=notebook_path,
                    companion_path=companion_path,
                ),
            ),
            self._markdown_cell(
                "understanding-heading",
                "## Dataset understanding\n\n"
                "Generate deterministic structure, semantic roles, and descriptive summaries.\n",
            ),
            self._code_cell(
                "dataset-understanding",
                "eda_result = edf.eda(dataset)\neda_result\n",
            ),
            self._markdown_cell(
                "planning-heading",
                "## EDA planning\n\nSelect and explain applicable follow-up analyses.\n",
            ),
            self._code_cell(
                "eda-planning",
                "eda_plan = edf.plan_eda(eda_result)\neda_plan\n",
            ),
            self._markdown_cell(
                "execution-heading",
                "## Plan execution\n\n"
                "Execute only the analyses selected by the deterministic plan.\n",
            ),
            self._code_cell(
                "plan-execution",
                "execution = edf.execute_eda(\n"
                "    dataset,\n"
                "    result=eda_result,\n"
                "    plan=eda_plan,\n"
                ")\n"
                "execution\n",
            ),
            self._markdown_cell(
                "workflow-heading",
                "## Complete Agentic EDA workflow\n\n"
                "Run understanding, planning, execution, and deterministic decisions together.\n",
            ),
            self._code_cell(
                "complete-workflow",
                self._workflow_source(
                    config=config,
                    config_was_supplied=config_was_supplied,
                ),
            ),
            self._markdown_cell(
                "findings-heading",
                "## Priority findings\n\nReview the highest-priority deterministic findings.\n",
            ),
            self._code_cell(
                "priority-findings",
                "workflow.priority_findings\n",
            ),
            self._markdown_cell(
                "actions-heading",
                "## Follow-up actions\n\nReview traceable recommended next actions.\n",
            ),
            self._code_cell(
                "follow-up-actions",
                "workflow.follow_up_actions\n",
            ),
            self._markdown_cell(
                "visualisations-heading",
                "## Visualisation recommendations\n\n"
                "Review deterministic chart recommendations and their source analyses.\n",
            ),
            self._code_cell(
                "visualisation-recommendations",
                "workflow.recommended_visualisations\n",
            ),
            self._markdown_cell(
                "questions-heading",
                "## Unresolved questions\n\n"
                "Review questions that require domain knowledge or human judgement.\n",
            ),
            self._code_cell(
                "unresolved-questions",
                "workflow.unresolved_questions\n",
            ),
            self._markdown_cell(
                "report-heading",
                "## Report export\n\n"
                "Export deterministic HTML and JSON reports and supported visualisations.\n",
            ),
            self._code_cell(
                "report-export",
                "report = edf.export_agentic_eda_report(\n"
                "    workflow,\n"
                "    dataset=dataset,\n"
                '    output_dir="agentic-eda-report",\n'
                ")\n"
                "report.generated_files\n",
            ),
        ]
        return {
            "cells": cells,
            "metadata": {
                "eazydatafix": {
                    "config": asdict(config),
                    "dataset_shape": list(workflow.eda_result.shape),
                    "deterministic": True,
                    "notebook_schema_version": 1,
                    "workflow_status": workflow.overall_status,
                },
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3",
                },
                "language_info": {
                    "name": "python",
                    "version": "3",
                },
            },
            "nbformat": _NOTEBOOK_FORMAT_VERSION,
            "nbformat_minor": _NOTEBOOK_FORMAT_MINOR_VERSION,
        }

    @staticmethod
    def _dataset_source(
        dataset: str | Path | pd.DataFrame,
        notebook_path: Path,
        companion_path: Path | None,
    ) -> str:
        if isinstance(dataset, pd.DataFrame):
            if companion_path is None:
                raise ValueError("DataFrame notebook exports require a companion dataset file.")

            path_source = AgenticEDANotebookExporter._portable_path_source(
                companion_path,
                notebook_path.parent,
            )
            return (
                f"{path_source}\n"
                'dataset = pd.read_json(dataset_path, orient="table")\n'
                "dataset.head()\n"
            )

        source_path = Path(dataset).expanduser().resolve()
        path_source = AgenticEDANotebookExporter._portable_path_source(
            source_path,
            notebook_path.parent,
        )
        return f"{path_source}\ndataset = dataset_path\ndataset_path\n"

    @staticmethod
    def _portable_path_source(
        source_path: Path,
        notebook_directory: Path,
    ) -> str:
        try:
            relative_path = Path(os.path.relpath(source_path, start=notebook_directory))
        except ValueError:
            relative_path = source_path

        relative_literal = json.dumps(str(relative_path), ensure_ascii=False)
        absolute_literal = json.dumps(str(source_path), ensure_ascii=False)
        return (
            f"dataset_path = Path({relative_literal})\n"
            "if not dataset_path.exists():\n"
            f"    dataset_path = Path({absolute_literal})"
        )

    @staticmethod
    def _workflow_source(
        config: AgenticEDAConfig,
        config_was_supplied: bool,
    ) -> str:
        if not config_was_supplied:
            config_source = "config = edf.AgenticEDAConfig()"
        else:
            settings = asdict(config)
            arguments = "\n".join(f"    {name}={value!r}," for name, value in settings.items())
            config_source = f"config = edf.AgenticEDAConfig(\n{arguments}\n)"

        return (
            f"{config_source}\n\n"
            "workflow = edf.run_agentic_eda(dataset, config=config)\n"
            "workflow\n"
        )

    @staticmethod
    def _markdown_cell(
        cell_id: str,
        source: str,
    ) -> dict[str, Any]:
        return {
            "cell_type": "markdown",
            "id": cell_id,
            "metadata": {},
            "source": source,
        }

    @staticmethod
    def _code_cell(
        cell_id: str,
        source: str,
    ) -> dict[str, Any]:
        return {
            "cell_type": "code",
            "execution_count": None,
            "id": cell_id,
            "metadata": {},
            "outputs": [],
            "source": source,
        }
