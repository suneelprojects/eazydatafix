"""Export the sample sales file as Power BI tables and a change log."""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import eazydatafix as edf


def _silence_dayfirst_parsing_warning() -> None:
    """Hide a repeated assessment warning for this recipe's day-first dates.

    The recipe parses ``%d/%m/%Y`` explicitly. Quality checks still call
    ``pandas.to_datetime`` without that format and warn on every pass.
    """
    warnings.filterwarnings(
        "ignore",
        message=r"Parsing dates in %d/%m/%Y format when dayfirst=False.*",
        category=UserWarning,
    )


def prepare(output_dir: Path) -> Path:
    """Preview, apply, and export the sample sales recipe.

    Args:
        output_dir: Directory for Power BI tables, the readiness report, and the change log.

    Returns:
        The output directory.
    """
    root = Path(__file__).resolve().parent
    _silence_dayfirst_parsing_warning()
    recipe = edf.PipelineRecipe.load(root / "recipe.json")
    source = root / "sales.csv"
    pipeline = edf.Pipeline(recipe)
    plan = pipeline.preview(source)
    result = pipeline.apply(source, plan)
    if not result.is_ready:
        raise RuntimeError("Sample sales pipeline is not ready. Inspect the printed issues.")
    output_dir.mkdir(parents=True, exist_ok=True)
    result.save(output_dir, formats=("csv", "excel"))
    _print_summary(result, output_dir)
    return output_dir


def _print_summary(result: edf.PipelineResult, output_dir: Path) -> None:
    """Print field types, row counts, quarantined ids, and the change log."""
    native = result.readiness_result
    print(f"Readiness score: {native.readiness_score}")
    print("Field types:")
    for table_name, fields in native.field_types.items():
        print(f"  {table_name}: {fields}")
    print("Rows:", {name: len(table) for name, table in result.tables.items()})
    rejected = result.rejected_rows.get("sales")
    if rejected is not None and not rejected.empty:
        print("Quarantined order ids:", ", ".join(rejected["Order ID"].astype(str)))
    print("Change log:")
    for change in result.changes:
        print(
            f"  {change.step}: rows {change.rows_before}->{change.rows_after}, "
            f"removed {change.removed_rows}, changed values {change.changed_values}"
        )
    print(f"Wrote {output_dir}")


def main(argv: list[str] | None = None) -> int:
    """Prepare the sample and return a process status code."""
    parser = argparse.ArgumentParser(description="Prepare the sample sales file for Power BI.")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Directory for tables, the readiness report, and the change log.",
    )
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parent
    try:
        prepare(args.output or (root / "output"))
    except (OSError, RuntimeError, ValueError, edf.EazyDataFixError) as error:
        print(error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
