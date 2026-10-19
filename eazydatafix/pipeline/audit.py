"""Deterministic fingerprints and bounded transformation evidence."""

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import numpy as np
import pandas as pd


def json_value(value: Any) -> Any:
    """Convert scalar and nested values into deterministic, strict JSON evidence."""
    if value is pd.NA or value is pd.NaT or value is None:
        return None
    if isinstance(value, np.generic):
        return json_value(value.item())
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None if math.isnan(value) else str(value)
    if isinstance(value, dict):
        return {
            str(key): json_value(item)
            for key, item in sorted(value.items(), key=lambda x: str(x[0]))
        }
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    if type(value) in {str, int, float, bool}:
        return value
    return str(value)


def digest(payload: Any) -> str:
    """Hash a canonical JSON payload rather than platform-dependent object hashes."""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def dataset_fingerprint(tables: dict[str, pd.DataFrame]) -> str:
    """Bind values, order, names and dtypes across all workflow tables."""
    parts = {}
    for name, table in sorted(tables.items()):
        # Stream rows into the hash to avoid materializing a second whole dataset.
        hasher = hashlib.sha256()
        metadata = {
            "columns": list(table.columns),
            "dtypes": [str(x) for x in table.dtypes],
            "rows": len(table),
        }
        hasher.update(json.dumps(metadata, sort_keys=True).encode())
        for row in table.itertuples(index=False, name=None):
            hasher.update(json.dumps(json_value(row), sort_keys=True, allow_nan=False).encode())
            hasher.update(b"\n")
        parts[name] = hasher.hexdigest()
    return digest(parts)


@dataclass(frozen=True, slots=True)
class PipelineIssue:
    """Describe a conversion, schema or readiness issue with source-row evidence."""

    code: str
    table: str
    column: str
    severity: str
    message: str
    count: int = 0
    samples: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True, slots=True)
class TransformationAudit:
    """Capture counts, dtype changes, removals and optional cell-level evidence."""

    step: str
    table: str
    rows_before: int
    rows_after: int
    columns_before: tuple[str, ...]
    columns_after: tuple[str, ...]
    changed_values: int
    dtype_changes: dict[str, tuple[str, str]]
    removed_rows: int
    added_rows: int
    samples: tuple[dict[str, Any], ...]
    details: tuple[dict[str, Any], ...] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe transformation evidence."""
        return json_value(asdict(self))


def audit_change(
    step: str,
    table: str,
    before: pd.DataFrame,
    after: pd.DataFrame,
    *,
    sample_size: int,
    detailed: bool,
) -> TransformationAudit | None:
    """Measure a transformation using source positions, independent of index labels."""
    if before.equals(after):
        return None
    examples: list[dict[str, Any]] = []
    details: list[dict[str, Any]] | None = [] if detailed else None
    changed = 0
    dtype_changes = {}

    def record(item: dict[str, Any]) -> None:
        if len(examples) < sample_size:
            examples.append(item)
        if details is not None:
            details.append(item)

    before_columns, after_columns = list(before.columns), list(after.columns)
    pairs = [(name, name) for name in before_columns if name in after_columns]
    if step.endswith("ColumnNormalizer") and len(before_columns) == len(after_columns):
        pairs = list(zip(before_columns, after_columns))
    common_rows = before.index.intersection(after.index, sort=False)
    for old, new in pairs:
        old_type, new_type = str(before[old].dtype), str(after[new].dtype)
        if old_type != new_type:
            dtype_changes[new] = (old_type, new_type)
        for position, left, right in zip(
            common_rows, before.loc[common_rows, old], after.loc[common_rows, new]
        ):
            left_json, right_json = json_value(left), json_value(right)
            if type(left_json) is type(right_json) and left_json == right_json:
                continue
            changed += 1
            record(
                {
                    "row_position": int(position),
                    "column": new,
                    "before": left_json,
                    "after": right_json,
                    "action": "changed",
                }
            )
    removed = before.index.difference(after.index, sort=False)
    added = after.index.difference(before.index, sort=False)
    for position in removed:
        record(
            {
                "row_position": int(position),
                "action": "removed",
                "before": json_value(before.loc[position].to_dict()),
            }
        )
    for position in added:
        record(
            {
                "row_position": int(position),
                "action": "added",
                "after": json_value(after.loc[position].to_dict()),
            }
        )
    for column in (name for name in after_columns if name not in before_columns):
        if step.endswith("ColumnNormalizer"):
            continue
        for position, value in after[column].items():
            changed += 1
            record(
                {
                    "row_position": int(position),
                    "column": column,
                    "after": json_value(value),
                    "action": "column_added",
                }
            )
    for column in (name for name in before_columns if name not in after_columns):
        if step.endswith("ColumnNormalizer"):
            continue
        for position, value in before[column].items():
            changed += 1
            record(
                {
                    "row_position": int(position),
                    "column": column,
                    "before": json_value(value),
                    "action": "column_removed",
                }
            )
    return TransformationAudit(
        step,
        table,
        len(before),
        len(after),
        tuple(before_columns),
        tuple(after_columns),
        changed,
        dtype_changes,
        len(removed),
        len(added),
        tuple(examples),
        tuple(details) if details is not None else None,
    )
