"""Command-line entry point for deterministic EazyDataFix workflows."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import eazydatafix as edf


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


def _run_one(dataset: Path, workflow: str) -> dict[str, object]:
    """Run one supported deterministic workflow and return a JSON-ready summary."""
    if workflow == "profile":
        result = edf.profile(dataset)
        return {"rows": result.rows, "columns": result.columns}
    if workflow == "assess":
        result = edf.assess(dataset)
        return {"quality_score": result.quality.score}
    if workflow == "fix":
        result = edf.fix(dataset)
        return {"rows": len(result.dataset), "columns": len(result.dataset.columns)}
    if workflow == "prepare":
        result = edf.prepare_with_report(dataset)
        return {"rows": len(result.dataset), "changes": result.changes}
    if workflow == "eda":
        result = edf.eda(dataset)
        return {"shape": list(result.shape), "summary": result.observations}
    if workflow == "agentic_eda":
        result = edf.run_agentic_eda(dataset)
        return {"status": result.status, "summary": result.summary}
    result = edf.run(dataset)
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
    arguments = parser.parse_args(argv)

    try:
        config = _load_config(arguments.config)
        workflow = str(config.get("workflow", "run"))
        configured_inputs = [Path(item) for item in config.get("inputs", [])]
        inputs = sorted({*arguments.inputs, *configured_inputs}, key=lambda path: str(path))
        if not inputs:
            raise ValueError("Provide at least one dataset path through inputs or configuration.")
        if workflow not in {"run", "profile", "assess", "fix", "prepare", "eda", "agentic_eda"}:
            raise ValueError("Unsupported workflow configuration.")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"edf configuration error: {error}", file=sys.stderr)
        return 2

    records: list[dict[str, object]] = []
    failures = 0
    for dataset in inputs:
        _log(
            {"event": "started", "dataset": str(dataset), "workflow": workflow}, arguments.log_file
        )
        try:
            summary = _run_one(dataset, workflow)
            record = {"dataset": str(dataset), "status": "passed", "summary": summary}
        except Exception as error:
            failures += 1
            record = {"dataset": str(dataset), "status": "failed", "error": str(error)}
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
