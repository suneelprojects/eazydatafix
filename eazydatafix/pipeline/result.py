"""Common pipeline results and self-contained preprocessing artifacts."""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from eazydatafix.exceptions import WorkflowError
from eazydatafix.models.ml_ready_result import MLPreprocessingArtifact
from eazydatafix.pipeline.audit import PipelineIssue, TransformationAudit, json_value
from eazydatafix.pipeline.recipe import PipelineRecipe


@dataclass(slots=True)
class RecipeMLArtifact:
    """Bundle stateless source preparation with training-fitted ML preprocessing."""

    recipe: PipelineRecipe
    preprocessing: MLPreprocessingArtifact

    def transform(self, dataset: str | Path | pd.DataFrame) -> pd.DataFrame:
        """Prepare new feature rows with saved rules, then use fitted parameters."""
        from eazydatafix.pipeline.engine import Pipeline

        result = Pipeline(self.recipe).run(dataset)
        if any(issue.severity == "error" for issue in result.issues):
            raise WorkflowError("Inference preparation failed; inspect the recipe rules.")
        if any(not table.empty for table in result.rejected_rows.values()):
            raise WorkflowError(
                "Inference would quarantine rows; correct inputs before predicting."
            )
        return self.preprocessing.transform(result.dataset)

    def to_dict(self) -> dict[str, Any]:
        """Return a versioned artifact containing both preparation and learned parameters."""
        return {
            "artifact_format_version": 1,
            "recipe": self.recipe.to_dict(),
            "preprocessing": self.preprocessing.to_dict(),
        }

    def to_json(self, path: str | Path) -> None:
        """Save a reusable recipe-bound ML artifact."""
        Path(path).write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    @classmethod
    def from_json(cls, path: str | Path) -> "RecipeMLArtifact":
        """Restore a recipe-bound artifact without loading executable objects."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if (
            type(data.get("artifact_format_version")) is not int
            or data["artifact_format_version"] != 1
        ):
            raise ValueError("Unsupported recipe-bound ML artifact format.")
        return cls(
            PipelineRecipe.from_dict(data["recipe"]),
            MLPreprocessingArtifact.from_dict(data["preprocessing"]),
        )


@dataclass(slots=True)
class PipelineResult:
    """Expose a common report/export interface while retaining native readiness results."""

    recipe: PipelineRecipe
    tables: dict[str, pd.DataFrame]
    rejected_rows: dict[str, pd.DataFrame]
    issues: list[PipelineIssue]
    changes: list[TransformationAudit]
    before_scores: dict[str, float]
    after_scores: dict[str, float]
    selected_steps: tuple[str, ...]
    skipped_steps: tuple[str, ...]
    source_fingerprint: str
    dry_run: bool = False
    readiness_result: Any = None
    artifact: RecipeMLArtifact | None = None
    validations: dict[str, Any] = field(default_factory=dict)
    integrity_fingerprint: str | None = field(default=None, repr=False)

    @property
    def dataset(self) -> pd.DataFrame:
        """Return the first prepared table; ML split datasets remain in readiness_result."""
        return next(iter(self.tables.values()))

    @property
    def is_ready(self) -> bool:
        """Require successful conversion, validation and the native readiness gate."""
        no_errors = not any(issue.severity == "error" for issue in self.issues)
        native_ready = self.readiness_result is not None and self.readiness_result.is_ready
        return bool(no_errors and native_ready)

    @property
    def status(self) -> str:
        """Return a shared pipeline status suitable for CLI and service callers."""
        return "ready" if self.is_ready else "failed"

    def report(self) -> dict[str, Any]:
        """Return strict JSON evidence with bounded examples and selected operations."""
        return json_value(
            {
                "report_format_version": 1,
                "recipe": self.recipe.to_dict(),
                "workflow": self.recipe.workflow,
                "status": self.status,
                "is_ready": self.is_ready,
                "dry_run": self.dry_run,
                "source_fingerprint": self.source_fingerprint,
                "selected_steps": self.selected_steps,
                "skipped_steps": self.skipped_steps,
                "before_scores": self.before_scores,
                "after_scores": self.after_scores,
                "tables": {
                    name: {
                        "rows": len(table),
                        "dtypes": {col: str(dtype) for col, dtype in table.dtypes.items()},
                    }
                    for name, table in self.tables.items()
                },
                "rejected_rows": {name: len(table) for name, table in self.rejected_rows.items()},
                "issues": [asdict(issue) for issue in self.issues],
                "changes": [change.to_dict() for change in self.changes],
                "validations": self.validations,
            }
        )

    def save(self, directory: str | Path, *, formats: tuple[str, ...] = ("csv",)) -> dict[str, Any]:
        """Export ready applied outputs plus evidence; preview/failed data cannot be exported."""
        from eazydatafix.pipeline.engine import _result_fingerprint

        if self.dry_run:
            raise WorkflowError("Preview data cannot be exported; apply the reviewed plan first.")
        if not self.is_ready:
            raise WorkflowError("Pipeline is not ready; inspect report() before exporting data.")
        if self.integrity_fingerprint != _result_fingerprint(self):
            raise WorkflowError("Pipeline outputs or evidence changed; run or review a new recipe.")
        if (
            not isinstance(formats, tuple)
            or not formats
            or any(x not in {"csv", "excel", "parquet"} for x in formats)
        ):
            raise ValueError("formats must contain csv, excel or parquet.")
        root = Path(directory)
        root.mkdir(parents=True, exist_ok=True)
        exported: dict[str, Any] = {}
        if self.recipe.workflow == "ml_ready":
            if formats != ("csv",):
                raise ValueError("ML split exports currently support CSV only.")
            exported["ml"] = self.readiness_result.save(root)
            self.artifact.to_json(root / "ml_ready_recipe_artifact.json")
        elif self.recipe.workflow == "powerbi_ready":
            exported.update(self.readiness_result.save(root, formats=formats))
        else:
            for name, table in self.tables.items():
                for export_format in dict.fromkeys(formats):
                    suffix = {"csv": ".csv", "excel": ".xlsx", "parquet": ".parquet"}[export_format]
                    path = root / f"{name}{suffix}"
                    if export_format == "csv":
                        table.to_csv(path, index=False)
                    elif export_format == "excel":
                        table.to_excel(path, index=False)
                    else:
                        table.to_parquet(path, index=False)
                    exported.setdefault(export_format, []).append(path)
        for name, table in self.rejected_rows.items():
            if not table.empty:
                table.to_csv(root / f"{name}_rejected.csv", index=False)
        report_path = root / "pipeline_report.json"
        report_path.write_text(
            json.dumps(self.report(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        self.recipe.save(root / "recipe.json")
        exported["report"] = report_path
        return exported


@dataclass(frozen=True, slots=True)
class PipelinePlan:
    """Bind a reviewed preview to its source, recipe, selected steps and outputs."""

    source_fingerprint: str
    recipe_fingerprint: str
    result_fingerprint: str
    selected_steps: tuple[str, ...]
    result: PipelineResult
