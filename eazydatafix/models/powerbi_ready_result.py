import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from eazydatafix.models.analysis_ready_result import AnalysisReadyResult
from eazydatafix.models.powerbi_ready_config import (
    PowerBIReadyConfig,
    PowerBIRelationship,
)


@dataclass(frozen=True, slots=True)
class PowerBIReadyIssue:
    """Describe a deterministic Power BI model or field issue."""

    code: str
    table: str
    column: str
    severity: str
    message: str
    action: str


@dataclass(slots=True)
class PowerBIReadyResult:
    """Return Power BI-compatible tables, model diagnostics, and exports."""

    tables: dict[str, pd.DataFrame]
    primary_table: str
    config: PowerBIReadyConfig
    analysis_ready_results: dict[str, AnalysisReadyResult]
    issues: list[PowerBIReadyIssue]
    changes: list[str]
    warnings: list[str]
    relationships: tuple[PowerBIRelationship, ...]
    field_types: dict[str, dict[str, str]]
    readiness_score: float

    @property
    def dataset(self) -> pd.DataFrame:
        """Return the primary prepared table for single-table convenience."""
        return self.tables[self.primary_table]

    @property
    def is_ready(self) -> bool:
        """Return whether all BI model gates pass the configured threshold."""
        has_errors = any(issue.severity == "error" for issue in self.issues)
        return (
            bool(self.tables)
            and all(not table.empty for table in self.tables.values())
            and self.readiness_score >= self.config.minimum_readiness_score
            and not has_errors
        )

    def report(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible readiness report."""
        return {
            "report_format_version": 1,
            "is_ready": self.is_ready,
            "readiness_score": self.readiness_score,
            "primary_table": self.primary_table,
            "tables": {
                name: {
                    "rows": len(table),
                    "columns": len(table.columns),
                    "field_types": self.field_types[name],
                }
                for name, table in self.tables.items()
            },
            "relationships": [asdict(relationship) for relationship in self.relationships],
            "issues": [asdict(issue) for issue in self.issues],
            "changes": list(self.changes),
            "warnings": list(self.warnings),
        }

    def save(
        self,
        directory: str | Path,
        *,
        formats: tuple[str, ...] = ("csv",),
        prefix: str = "powerbi_ready",
    ) -> dict[str, tuple[Path, ...]]:
        """Export tables as CSV, Excel, or Parquet plus a JSON readiness report."""
        supported = {"csv", "excel", "parquet"}
        if not isinstance(formats, tuple) or not formats:
            raise ValueError("formats must be a non-empty tuple.")
        unknown = [value for value in formats if value not in supported]
        if unknown:
            raise ValueError("Unsupported Power BI export format(s): " + ", ".join(unknown))

        output_directory = Path(directory)
        output_directory.mkdir(parents=True, exist_ok=True)
        exported: dict[str, tuple[Path, ...]] = {}

        for export_format in dict.fromkeys(formats):
            if export_format == "csv":
                paths = []
                for table_name, table in self.tables.items():
                    path = output_directory / f"{prefix}_{table_name}.csv"
                    table.to_csv(path, index=False)
                    paths.append(path)
                exported[export_format] = tuple(paths)
            elif export_format == "excel":
                path = output_directory / f"{prefix}.xlsx"
                sheet_names: list[str] = []
                with pd.ExcelWriter(path, engine="openpyxl") as writer:
                    for table_name, table in self.tables.items():
                        base_name = table_name[:31]
                        sheet_name = base_name
                        suffix = 2
                        while sheet_name.casefold() in {
                            existing.casefold() for existing in sheet_names
                        }:
                            ending = f"_{suffix}"
                            sheet_name = f"{base_name[: 31 - len(ending)]}{ending}"
                            suffix += 1
                        sheet_names.append(sheet_name)
                        table.to_excel(writer, sheet_name=sheet_name, index=False)
                exported[export_format] = (path,)
            else:
                paths = []
                for table_name, table in self.tables.items():
                    path = output_directory / f"{prefix}_{table_name}.parquet"
                    try:
                        table.to_parquet(path, index=False)
                    except ImportError as error:
                        raise ImportError(
                            'Install Parquet support with: pip install "eazydatafix[parquet]"'
                        ) from error
                    paths.append(path)
                exported[export_format] = tuple(paths)

        report_path = output_directory / f"{prefix}_readiness.json"
        report_path.write_text(
            json.dumps(self.report(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        exported["report"] = (report_path,)
        return exported
