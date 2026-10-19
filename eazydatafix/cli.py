"""Command-line entry point for deterministic EazyDataFix workflows."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import eazydatafix as edf
from eazydatafix.pipeline.recipe import _decode


def _load_config(path: Path | None) -> dict[str, Any]:
    """Load JSON or optional YAML configuration into a mapping."""
    if path is None:
        return {}
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
    elif path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as error:
            raise ValueError("YAML configuration requires the 'yaml' extra.") from error
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    else:
        raise ValueError("Configuration must use a .json, .yaml, or .yml suffix.")
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Configuration root must be an object or mapping.")
    return data


def _log(event: dict[str, object], log_file: Path | None) -> None:
    """Write one stable JSON log event to an optional log file."""
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")


def _run_one(
    dataset: Path,
    workflow: str,
    configs: dict[str, Any],
    export_dir: Path | None = None,
    formats: tuple[str, ...] = ("csv",),
) -> dict[str, object]:
    """Run one supported deterministic workflow and return a JSON-ready summary."""
    if workflow == "profile":
        result = edf.profile(dataset)
        return {"rows": result.rows, "columns": result.columns}
    if workflow == "assess":
        result = edf.assess(dataset)
        return {"quality_score": result.quality.score}
    if workflow == "fix":
        result = edf.fix(dataset, configs.get("fix_config"))
        if export_dir is not None:
            export_dir.mkdir(parents=True, exist_ok=True)
            result.dataset.to_csv(export_dir / "clean.csv", index=False)
        return {"rows": len(result.dataset), "columns": len(result.dataset.columns)}
    if workflow == "prepare":
        result = edf.prepare_with_report(dataset, configs.get("prepare_config"))
        return {"rows": len(result.dataset), "changes": result.changes}
    if workflow in {"analysis_ready", "ml_ready", "powerbi_ready"}:
        if workflow == "analysis_ready":
            result = edf.analysis_ready_with_report(dataset, configs.get("analysis_ready_config"))
            summary = {
                "is_ready": result.is_ready,
                "before_score": result.before_score,
                "after_score": result.after_score,
                "changes": result.changes,
            }
        elif workflow == "ml_ready":
            result = edf.ml_ready(
                dataset, target=configs["target"], config=configs.get("ml_config")
            )
            summary = {
                "is_ready": result.is_ready,
                "readiness_score": result.readiness_score,
                "feature_names": result.feature_names,
                "changes": result.changes,
            }
        else:
            result = edf.powerbi_ready(dataset, configs.get("powerbi_config"))
            summary = result.report()
        if export_dir is not None and result.is_ready:
            export_dir.mkdir(parents=True, exist_ok=True)
            if workflow == "analysis_ready":
                result.save(export_dir / "analysis_ready.csv")
            elif workflow == "powerbi_ready":
                result.save(export_dir, formats=formats)
            else:
                result.save(export_dir)
        return summary
    if workflow == "eda":
        result = edf.eda(dataset)
        return {"shape": list(result.shape), "summary": result.observations}
    if workflow == "agentic_eda":
        result = edf.run_agentic_eda(dataset)
        return {"status": result.status, "summary": result.summary}
    result = edf.run(dataset, configs.get("fix_config"))
    return {"shape": list(result.eda_result.shape), "fixes": result.fix_result.applied_fixes}


def main(argv: list[str] | None = None) -> int:
    """Run configured datasets and return a pipeline-safe process exit code."""
    parser = argparse.ArgumentParser(
        prog="edf", description="Run deterministic EazyDataFix workflows."
    )
    parser.add_argument("inputs", nargs="*", type=Path, help="Dataset paths to process.")
    parser.add_argument("--config", type=Path, help="JSON or YAML workflow configuration.")
    parser.add_argument("--output", type=Path, help="Write a JSON batch summary to this file.")
    parser.add_argument(
        "--log-file", type=Path, help="Write structured JSON-line events to this file."
    )
    parser.add_argument("--recipe", type=Path, help="Run a versioned JSON/YAML pipeline recipe.")
    parser.add_argument(
        "--preview", action="store_true", help="Preview recipe changes without exporting data."
    )
    parser.add_argument(
        "--export-dir", type=Path, help="Export ready datasets and pipeline evidence."
    )
    parser.add_argument(
        "--format",
        dest="formats",
        action="append",
        choices=["csv", "excel", "parquet"],
        help="Recipe/Power BI export format; defaults to CSV.",
    )
    parser.add_argument(
        "--select-step", action="append", help="Select recipe step IDs; readiness is mandatory."
    )
    parser.add_argument(
        "--table",
        action="append",
        default=[],
        metavar="NAME=PATH",
        help="Named Power BI table for a multi-table recipe.",
    )
    arguments = parser.parse_args(argv)

    try:
        config = _load_config(arguments.config)
        if arguments.recipe is not None and arguments.config is not None:
            raise ValueError("Use either --recipe or --config.")
        if not arguments.recipe and (arguments.preview or arguments.select_step or arguments.table):
            raise ValueError("--preview, --select-step and --table require --recipe.")
        recipe = edf.PipelineRecipe.load(arguments.recipe) if arguments.recipe else None
        configs = {}
        for name, model in (
            ("fix_config", edf.FixConfig),
            ("prepare_config", edf.PrepareConfig),
            ("analysis_ready_config", edf.AnalysisReadyConfig),
            ("ml_config", edf.MLReadyConfig),
            ("powerbi_config", edf.PowerBIReadyConfig),
        ):
            if name in config:
                configs[name] = _decode(model, config[name], name)
        workflow = str(config.get("workflow", "run"))
        if recipe:
            workflow = recipe.workflow
        if workflow == "ml_ready" and not recipe:
            if not isinstance(config.get("target"), str) or not config["target"].strip():
                raise ValueError("ml_ready requires a non-empty target in --config.")
            configs["target"] = config["target"]
        if not isinstance(config.get("inputs", []), list) or any(
            not isinstance(value, str) for value in config.get("inputs", [])
        ):
            raise ValueError("inputs must be an array of file paths.")
        configured_inputs = [Path(item) for item in config.get("inputs", [])]
        inputs = sorted({*arguments.inputs, *configured_inputs}, key=lambda path: str(path))
        tables = {}
        for entry in arguments.table:
            name, separator, path = entry.partition("=")
            if not separator or not name or not path or name in tables:
                raise ValueError("Each --table must have a unique NAME=PATH.")
            tables[name] = Path(path)
        if tables and (inputs or recipe.workflow != "powerbi_ready"):
            raise ValueError(
                "Named tables require a Power BI recipe and cannot be mixed with input paths."
            )
        if not inputs and not tables:
            raise ValueError("Provide at least one dataset path through inputs or configuration.")
        if workflow not in {
            "run",
            "profile",
            "assess",
            "fix",
            "prepare",
            "eda",
            "agentic_eda",
            "analysis_ready",
            "ml_ready",
            "powerbi_ready",
        }:
            raise ValueError("Unsupported workflow configuration.")
        if recipe:
            pipeline = edf.Pipeline(recipe)
        formats = tuple(arguments.formats or ["csv"])
    except (OSError, TypeError, ValueError, ImportError) as error:
        print(f"edf configuration error: {error}", file=sys.stderr)
        return 2

    records: list[dict[str, object]] = []
    failures = 0
    jobs = [(str(path), path) for path in inputs] if not tables else [("model", tables)]
    # Stable numbering avoids export collisions for files with the same basename.
    for position, (label, dataset) in enumerate(jobs):
        _log({"event": "started", "dataset": label, "workflow": workflow}, arguments.log_file)
        try:
            export_dir = (
                arguments.export_dir / f"{position + 1:03d}_{Path(label).stem}"
                if arguments.export_dir
                else None
            )
            if recipe:
                plan = pipeline.preview(dataset, selected_steps=arguments.select_step)
                result = plan.result if arguments.preview else pipeline.apply(dataset, plan)
                summary = result.report()
                if export_dir is not None:
                    export_dir.mkdir(parents=True, exist_ok=True)
                    (export_dir / "pipeline_report.json").write_text(
                        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
                    )
                    if not arguments.preview and result.is_ready:
                        result.save(export_dir, formats=formats)
            else:
                summary = _run_one(dataset, workflow, configs, export_dir, formats)
            passed = summary.get("is_ready", True)
            failures += int(not passed)
            record = {
                "dataset": label,
                "status": "passed" if passed else "failed",
                "summary": summary,
            }
        except Exception as error:
            failures += 1
            record = {"dataset": label, "status": "failed", "error": str(error)}
        records.append(record)
        _log({"event": "completed", **record}, arguments.log_file)

    output = {"workflow": workflow, "records": records, "passed": failures == 0}
    rendered = json.dumps(output, indent=2, sort_keys=True, default=str)
    if arguments.output is None:
        print(rendered)
    else:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
