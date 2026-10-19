"""Compose the existing cleaning, preparation and readiness engines with recipes."""

from __future__ import annotations

import csv
import json
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

import pandas as pd

from eazydatafix.assessment.engine import AssessmentEngine
from eazydatafix.core.dataset_loader import DatasetLoader
from eazydatafix.exceptions import WorkflowError
from eazydatafix.fix.column_normalizer import ColumnNormalizer
from eazydatafix.fix.engine import FixEngine
from eazydatafix.models.analysis_ready_config import AnalysisReadyConfig
from eazydatafix.models.data_contract import DataContract
from eazydatafix.models.fix_config import FixConfig
from eazydatafix.models.prepare_config import PrepareConfig
from eazydatafix.pipeline.audit import (
    PipelineIssue,
    TransformationAudit,
    audit_change,
    dataset_fingerprint,
    digest,
    json_value,
)
from eazydatafix.pipeline.conversion import ExplicitConverter
from eazydatafix.pipeline.recipe import ColumnRule, PipelineRecipe
from eazydatafix.pipeline.result import PipelinePlan, PipelineResult, RecipeMLArtifact
from eazydatafix.prepare.engine import PrepareEngine
from eazydatafix.readiness.analysis import AnalysisReadyEngine
from eazydatafix.readiness.ml import MLReadyEngine
from eazydatafix.readiness.powerbi import PowerBIReadyEngine
from eazydatafix.validation.contracts import ContractEngine

DatasetInput = str | Path | pd.DataFrame
PipelineInput = DatasetInput | Mapping[str, DatasetInput]


def _load_source(source: DatasetInput) -> pd.DataFrame:
    """Preserve CSV/Excel tokens before declared conversion, including leading zeroes."""
    if isinstance(source, (str, Path)):
        path = Path(source)
        if path.suffix.lower() == ".csv":
            with path.open(encoding="utf-8-sig", newline="") as stream:
                header = next(csv.reader(stream), [])
            if len(header) != len(set(header)):
                raise ValueError("CSV inputs require unique column headings.")
            dataframe = pd.read_csv(path, dtype=object, keep_default_na=False)
        elif path.suffix.lower() in {".xlsx", ".xls"}:
            headings = pd.read_excel(path, header=None, nrows=1, keep_default_na=False)
            header = headings.iloc[0].tolist() if not headings.empty else []
            if len(header) != len(set(header)):
                raise ValueError("Excel inputs require unique column headings.")
            dataframe = pd.read_excel(path, dtype=object, keep_default_na=False)
        else:
            dataframe = DatasetLoader.load(source)
    else:
        dataframe = DatasetLoader.load(source)
    if not dataframe.columns.is_unique or any(not isinstance(x, str) for x in dataframe.columns):
        raise ValueError("Pipeline inputs require unique string column names.")
    return dataframe.copy(deep=True).reset_index(drop=True)


def _result_fingerprint(result: PipelineResult) -> str:
    payload: dict[str, Any] = {
        "tables": dataset_fingerprint(result.tables),
        "rejected": dataset_fingerprint(result.rejected_rows),
        "report": result.report(),
    }
    native = result.readiness_result
    if result.recipe.workflow == "ml_ready" and native is not None:
        payload["ml"] = dataset_fingerprint(
            {"train": native.train_dataset, "test": native.test_dataset}
        )
        payload["artifact"] = result.artifact.to_dict()
    elif result.recipe.workflow == "powerbi_ready" and native is not None:
        payload["powerbi"] = native.report()
    return digest(payload)


class Pipeline:
    """Preview, apply and repeat a declared data-preparation workflow."""

    def __init__(self, recipe: PipelineRecipe) -> None:
        """Snapshot the recipe so external config mutations cannot change reviewed rules."""
        if not isinstance(recipe, PipelineRecipe):
            raise TypeError("recipe must be PipelineRecipe.")
        self._recipe_json = json.dumps(recipe.to_dict(), sort_keys=True)
        # Round-trip also validates direct Python configurations with the strict schema.
        PipelineRecipe.from_dict(json.loads(self._recipe_json))

    @property
    def recipe(self) -> PipelineRecipe:
        """Return a detached recipe snapshot."""
        return PipelineRecipe.from_dict(json.loads(self._recipe_json))

    def preview(
        self,
        dataset: PipelineInput,
        *,
        selected_steps: Sequence[str] | None = None,
    ) -> PipelinePlan:
        """Execute a non-mutating preview and bind it to source and result fingerprints."""
        sources = self._load(dataset)
        result = self._execute(sources, selected_steps=selected_steps, dry_run=True)
        return PipelinePlan(
            result.source_fingerprint,
            digest(self.recipe.to_dict()),
            _result_fingerprint(result),
            result.selected_steps,
            result,
        )

    def apply(self, dataset: PipelineInput, plan: PipelinePlan) -> PipelineResult:
        """Replay exactly the reviewed selection, rejecting changed data, rules or evidence."""
        if not isinstance(plan, PipelinePlan):
            raise TypeError("plan must be a PipelinePlan returned by preview().")
        sources = self._load(dataset)
        if dataset_fingerprint(sources) != plan.source_fingerprint:
            raise WorkflowError("Source dataset changed after preview; create a new preview.")
        if digest(self.recipe.to_dict()) != plan.recipe_fingerprint:
            raise WorkflowError("Recipe changed after preview; create a new preview.")
        if _result_fingerprint(plan.result) != plan.result_fingerprint:
            raise WorkflowError("Preview evidence was modified; create a new preview.")
        result = self._execute(sources, selected_steps=plan.selected_steps, dry_run=True)
        if _result_fingerprint(result) != plan.result_fingerprint:
            raise WorkflowError(
                "Reviewed output no longer matches execution; create a new preview."
            )
        result.dry_run = False
        result.integrity_fingerprint = _result_fingerprint(result)
        return result

    def run(self, dataset: PipelineInput) -> PipelineResult:
        """Apply the full declared recipe for explicit, repeatable batch processing."""
        return self._execute(self._load(dataset), selected_steps=None, dry_run=False)

    def _load(self, dataset: PipelineInput) -> dict[str, pd.DataFrame]:
        recipe = self.recipe
        if isinstance(dataset, Mapping):
            if recipe.workflow != "powerbi_ready" or not dataset:
                raise ValueError("Multi-table inputs require a non-empty Power BI recipe.")
            sources = {}
            for name, source in sorted(dataset.items()):
                if not isinstance(name, str) or not name.strip():
                    raise ValueError("Table names must be non-empty strings.")
                normalized = ColumnNormalizer.normalize_name(name)
                if not normalized or normalized in sources:
                    raise ValueError("Table names collide or are empty after normalization.")
                sources[normalized] = _load_source(source)
        else:
            name = (
                recipe.powerbi_config.table_name if recipe.workflow == "powerbi_ready" else "data"
            )
            name = ColumnNormalizer.normalize_name(name)
            if not name:
                raise ValueError("Table name must normalize to a non-empty name.")
            sources = {name: _load_source(dataset)}
        unknown = set(recipe.table_columns) - set(sources)
        if unknown:
            raise ValueError("Recipe references missing table(s): " + ", ".join(sorted(unknown)))
        return sources

    def _steps(self, sources: dict[str, pd.DataFrame]) -> tuple[str, ...]:
        recipe = self.recipe
        operations = []
        for table in sources:
            operations.append(f"{table}/clean")
            rules = {**recipe.columns, **recipe.table_columns.get(table, {})}
            operations.extend(f"{table}/column:{column}" for column in sorted(rules))
            operations.extend((f"{table}/finish", f"{table}/prepare"))
        return (*operations, "readiness")

    def _selection(
        self,
        sources: dict[str, pd.DataFrame],
        selected: Sequence[str] | None,
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        steps = self._steps(sources)
        if selected is None:
            return steps, ()
        if isinstance(selected, str) or any(not isinstance(x, str) for x in selected):
            raise ValueError("selected_steps must be a sequence of step IDs.")
        unknown = set(selected) - set(steps)
        if unknown or len(selected) != len(set(selected)):
            raise ValueError("selected_steps contains unknown or duplicate step IDs.")
        if "readiness" not in selected:
            raise ValueError("The readiness/validation step cannot be skipped.")
        # Column rules use names and missing markers from the cleaning stage.
        for table in sources:
            if (
                any(x.startswith(f"{table}/column:") for x in selected)
                and f"{table}/clean" not in selected
            ):
                raise ValueError(
                    "Column rules require the table's clean step; re-preview the selection."
                )
        return (
            tuple(x for x in steps if x in selected),
            tuple(x for x in steps if x not in selected),
        )

    def _execute(
        self,
        sources: dict[str, pd.DataFrame],
        *,
        selected_steps: Sequence[str] | None,
        dry_run: bool,
    ) -> PipelineResult:
        recipe = self.recipe
        selected, skipped = self._selection(sources, selected_steps)
        prepared: dict[str, pd.DataFrame] = {}
        rejected: dict[str, pd.DataFrame] = {}
        issues: list[PipelineIssue] = []
        changes: list[TransformationAudit] = []
        before_scores, after_scores = {}, {}
        assessment = AssessmentEngine()

        def audit(table: str, step: str, before: pd.DataFrame, after: pd.DataFrame) -> None:
            evidence = audit_change(
                step,
                table,
                before,
                after,
                sample_size=recipe.audit_sample_size,
                detailed=recipe.detailed_audit,
            )
            if evidence is not None:
                changes.append(evidence)

        for table, source in sources.items():
            candidate = source.copy()
            if recipe.fix_config.normalize_column_names and f"{table}/clean" in selected:
                normalized = [ColumnNormalizer.normalize_name(name) for name in source.columns]
                if not all(normalized) or len(normalized) != len(set(normalized)):
                    raise ValueError(
                        f"Column headings in '{table}' collide or normalize to empty names; "
                        "rename them before running the recipe."
                    )
            before_scores[table] = assessment.assess_dataframe(
                source, file_name=table
            ).quality.score
            rules = {**recipe.columns, **recipe.table_columns.get(table, {})}
            protected = tuple(sorted(rules))
            if f"{table}/clean" in selected:
                config = replace(
                    recipe.fix_config,
                    remove_duplicates=False,
                    remove_empty_rows=False,
                    remove_empty_columns=False,
                    missing_value_strategy="keep",
                    column_rules={
                        name: replace(rule, missing_value_strategy="keep")
                        for name, rule in recipe.fix_config.column_rules.items()
                    },
                    protected_columns=(*recipe.fix_config.protected_columns, *protected),
                )
                candidate = (
                    FixEngine()
                    .fix(
                        candidate,
                        config,
                        observer=lambda step, left, right: audit(
                            table, f"clean/{step}", left, right
                        ),
                    )
                    .dataset
                )
            rejected_positions: set[int] = set()
            for column, rule in sorted(rules.items()):
                if f"{table}/column:{column}" not in selected:
                    continue
                before = candidate.copy()
                candidate, positions = self._column(candidate, table, column, rule, issues)
                rejected_positions.update(positions)
                audit(table, f"column:{column}", before, candidate)
            rejected[table] = source.loc[sorted(rejected_positions)].copy()
            if f"{table}/finish" in selected and not candidate.empty:
                config = replace(
                    recipe.fix_config,
                    normalize_column_names=False,
                    trim_whitespace=False,
                    missing_markers=(),
                    convert_data_types=False,
                    column_rules={
                        name: replace(rule, missing_markers=(), trim_whitespace=False)
                        for name, rule in recipe.fix_config.column_rules.items()
                    },
                )
                candidate = (
                    FixEngine()
                    .fix(
                        candidate,
                        config,
                        observer=lambda step, left, right: audit(
                            table, f"finish/{step}", left, right
                        ),
                    )
                    .dataset
                )
            if f"{table}/prepare" in selected and not candidate.empty:
                before = candidate.copy()
                config = replace(
                    recipe.prepare_config,
                    protected_columns=(*recipe.prepare_config.protected_columns, *protected),
                )
                preparation = PrepareEngine().prepare_with_report(candidate, config)
                candidate = preparation.dataset
                audit(table, "prepare", before, candidate)
                issues.extend(
                    PipelineIssue("preparation_warning", table, "", "warning", message)
                    for message in preparation.warnings
                )
            prepared[table] = candidate
            if candidate.empty or not len(candidate.columns):
                issues.append(
                    PipelineIssue(
                        "empty_dataset", table, "", "error", "No usable rows or columns remain."
                    )
                )
                after_scores[table] = 0.0
            else:
                after_scores[table] = assessment.assess_dataframe(
                    candidate, file_name=table
                ).quality.score

        validations = {}
        for table, candidate in prepared.items():
            if not candidate.empty:
                validation = ContractEngine().validate(
                    candidate, recipe.contract or DataContract(()), recipe.quality_rules
                )
                validations[table] = validation.to_dict()
                issues.extend(
                    PipelineIssue(
                        "contract_failed", table, item.column or "", "error", item.message
                    )
                    for item in validation.results
                    if not item.passed
                )

        native = None
        artifact = None
        if all(not value.empty and len(value.columns) for value in prepared.values()) and not any(
            x.severity == "error" for x in issues
        ):
            native, artifact = self._readiness(prepared, selected)
            for issue in native.issues:
                issues.append(
                    PipelineIssue(
                        issue.code,
                        getattr(issue, "table", next(iter(prepared))),
                        issue.column,
                        issue.severity,
                        issue.message,
                    )
                )
            if recipe.workflow == "powerbi_ready":
                for table, output in native.tables.items():
                    before = prepared.get(table, pd.DataFrame(index=output.index))
                    audit(table, "powerbi_ready", before.reset_index(drop=True), output)
                prepared = native.tables
                after_scores = {
                    name: assessment.assess_dataframe(frame, file_name=name).quality.score
                    for name, frame in prepared.items()
                    if not frame.empty
                }
        result = PipelineResult(
            recipe,
            prepared,
            rejected,
            issues,
            changes,
            before_scores,
            after_scores,
            selected,
            skipped,
            dataset_fingerprint(sources),
            dry_run,
            native,
            artifact,
            validations,
        )
        result.integrity_fingerprint = _result_fingerprint(result)
        return result

    def _column(
        self,
        candidate: pd.DataFrame,
        table: str,
        column: str,
        rule: ColumnRule,
        issues: list[PipelineIssue],
    ) -> tuple[pd.DataFrame, set[int]]:
        if column not in candidate:
            if rule.required:
                issues.append(
                    PipelineIssue(
                        "missing_column",
                        table,
                        column,
                        "error",
                        "Required recipe column is missing.",
                    )
                )
            return candidate, set()
        conversion = ExplicitConverter.convert(candidate[column], rule)
        count = int(conversion.invalid.sum())
        positions = set()
        if count:
            samples = tuple(
                {
                    "row_position": int(position),
                    "value": json_value(candidate.at[position, column]),
                    "reason": conversion.reason,
                }
                for position in candidate.index[conversion.invalid][: self.recipe.audit_sample_size]
            )
            issues.append(
                PipelineIssue(
                    "conversion_failed",
                    table,
                    column,
                    "error" if rule.on_error == "reject" else "warning",
                    f"{count} invalid value(s); policy={rule.on_error}. {conversion.reason}",
                    count,
                    samples,
                )
            )
            if rule.on_error in {"preserve", "reject"}:
                # Preserve the entire column rather than return mixed, deceptively typed values.
                return candidate, positions
            positions = set(int(x) for x in candidate.index[conversion.invalid])
            candidate = candidate.loc[~conversion.invalid].copy()
        candidate[column] = conversion.values.loc[candidate.index]
        return candidate, positions

    def _readiness(
        self,
        prepared: dict[str, pd.DataFrame],
        selected: tuple[str, ...],
    ) -> tuple[Any, RecipeMLArtifact | None]:
        recipe = self.recipe
        # Readiness engines assess/validate the already prepared values without re-cleaning them.
        analysis_config = AnalysisReadyConfig(
            fix_config=FixConfig(
                missing_value_strategy="keep",
                missing_markers=(),
                normalize_column_names=False,
                trim_whitespace=False,
                convert_data_types=False,
                remove_duplicates=False,
                remove_empty_rows=False,
                remove_empty_columns=False,
            ),
            prepare_config=PrepareConfig(infer_types=False),
        )
        if recipe.workflow == "analysis_ready":
            return AnalysisReadyEngine().run(next(iter(prepared.values())), analysis_config), None
        if recipe.workflow == "powerbi_ready":
            config = replace(recipe.powerbi_config, analysis_ready_config=analysis_config)
            return PowerBIReadyEngine().run(prepared, config), None
        config = replace(recipe.ml_config, analysis_ready_config=analysis_config)
        native = MLReadyEngine().run(
            next(iter(prepared.values())), target=recipe.target, config=config
        )
        # Inference cannot drop or impute rows and need not contain the supervised target.
        rules = {
            column: replace(rule, required=False) if column == native.target else rule
            for column, rule in recipe.columns.items()
        }
        inference_recipe = replace(
            recipe,
            workflow="analysis_ready",
            target=None,
            columns=rules,
            fix_config=replace(
                recipe.fix_config,
                remove_duplicates=False,
                remove_empty_rows=False,
                remove_empty_columns=False,
            ),
            contract=None,
            quality_rules=(),
        )
        # Save only the approved preparation stages in the artifact, not rejected transformations.
        if "data/clean" not in selected:
            inference_recipe = replace(inference_recipe, fix_config=analysis_config.fix_config)
        if "data/prepare" not in selected:
            inference_recipe = replace(
                inference_recipe, prepare_config=analysis_config.prepare_config
            )
        inference_recipe = replace(
            inference_recipe,
            columns={
                key: value
                for key, value in inference_recipe.columns.items()
                if f"data/column:{key}" in selected
            },
        )
        return native, RecipeMLArtifact(inference_recipe, native.artifact)
