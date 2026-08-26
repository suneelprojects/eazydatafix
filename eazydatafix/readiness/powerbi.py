import json
from collections.abc import Mapping
from pathlib import Path
from typing import TypeAlias

import pandas as pd

from eazydatafix.core.dataset_loader import DatasetLoader
from eazydatafix.fix.column_normalizer import ColumnNormalizer
from eazydatafix.models.powerbi_ready_config import (
    PowerBIKey,
    PowerBIReadyConfig,
    PowerBIRelationship,
)
from eazydatafix.models.powerbi_ready_result import (
    PowerBIReadyIssue,
    PowerBIReadyResult,
)
from eazydatafix.readiness.analysis import AnalysisReadyEngine

DatasetInput: TypeAlias = str | Path | pd.DataFrame
PowerBIInput: TypeAlias = DatasetInput | Mapping[str, DatasetInput]


class PowerBIReadyEngine:
    """Compose Analysis Ready transformations with Power BI model validation."""

    def __init__(self) -> None:
        self._analysis_ready_engine = AnalysisReadyEngine()

    def run(
        self,
        dataset: PowerBIInput,
        config: PowerBIReadyConfig | None = None,
    ) -> PowerBIReadyResult:
        """Prepare one or more datasets for import into a Power BI model."""
        config = config or PowerBIReadyConfig()
        sources, primary_table = self._load_sources(dataset, config.table_name)
        tables: dict[str, pd.DataFrame] = {}
        analysis_results = {}
        issues: list[PowerBIReadyIssue] = []
        changes: list[str] = []
        warnings: list[str] = []

        for table_name, source in sources.items():
            flattened, flatten_changes, flatten_issues = self._flatten_table(
                source,
                table_name,
                enabled=config.flatten_nested,
            )
            analysis_result = self._analysis_ready_engine.run(
                flattened,
                config.analysis_ready_config,
            )
            prepared, type_changes = self._coerce_field_types(
                analysis_result.dataset,
                table_name,
            )
            tables[table_name] = prepared
            analysis_results[table_name] = analysis_result
            changes.extend(flatten_changes)
            changes.extend(f"[{table_name}] {change}" for change in analysis_result.changes)
            changes.extend(type_changes)
            issues.extend(flatten_issues)
            issues.extend(self._analysis_issues(table_name, analysis_result.issues))
            warnings.extend(analysis_result.warnings)

        relationships = tuple(
            self._normalize_relationship(relationship) for relationship in config.relationships
        )
        if config.generate_date_table:
            date_table_name = self._normalize_name(config.date_table_name, fallback="date")
            if date_table_name in tables:
                issues.append(
                    self._issue(
                        "date_table_collision",
                        date_table_name,
                        "",
                        "error",
                        f"Canonical date table '{date_table_name}' conflicts with an input table.",
                        "Choose a distinct date_table_name.",
                    )
                )
            else:
                date_table, date_relationships, date_changes, date_issues = self._build_date_table(
                    tables, config, date_table_name
                )
                issues.extend(date_issues)
                changes.extend(date_changes)
                if date_table is not None:
                    tables[date_table_name] = date_table
                    relationships = (*relationships, *date_relationships)

        normalized_keys = tuple(self._normalize_key(key) for key in config.keys)
        if config.generate_date_table:
            date_table_name = self._normalize_name(config.date_table_name, fallback="date")
            if date_table_name in tables:
                normalized_keys = (
                    *normalized_keys,
                    PowerBIKey(table=date_table_name, columns=("date",)),
                )

        issues.extend(self._validate_keys(tables, normalized_keys))
        issues.extend(self._validate_relationships(tables, relationships))
        field_types = {
            table_name: {column: self._powerbi_type(table[column]) for column in table.columns}
            for table_name, table in tables.items()
        }
        warnings.extend(issue.message for issue in issues if issue.severity != "info")
        warnings = list(dict.fromkeys(warnings))

        return PowerBIReadyResult(
            tables=tables,
            primary_table=primary_table,
            config=config,
            analysis_ready_results=analysis_results,
            issues=issues,
            changes=list(dict.fromkeys(changes)),
            warnings=warnings,
            relationships=relationships,
            field_types=field_types,
            readiness_score=self._readiness_score(issues),
        )

    def _load_sources(
        self,
        dataset: PowerBIInput,
        default_table_name: str,
    ) -> tuple[dict[str, pd.DataFrame], str]:
        """Load caller-owned inputs into independent, deterministically named tables."""
        if isinstance(dataset, Mapping):
            if not dataset:
                raise ValueError("Power BI Ready requires at least one input table.")
            sources: dict[str, pd.DataFrame] = {}
            for raw_name, value in dataset.items():
                if not isinstance(raw_name, str) or not raw_name.strip():
                    raise ValueError("Power BI table names must be non-empty strings.")
                table_name = self._normalize_name(raw_name, fallback="table")
                if table_name in sources:
                    raise ValueError(
                        f"Power BI table names collide after normalization: '{table_name}'."
                    )
                sources[table_name] = DatasetLoader.load(value).copy(deep=True)
            return sources, next(iter(sources))

        table_name = self._normalize_name(default_table_name, fallback="data")
        return {table_name: DatasetLoader.load(dataset).copy(deep=True)}, table_name

    def _flatten_table(
        self,
        dataframe: pd.DataFrame,
        table_name: str,
        *,
        enabled: bool,
    ) -> tuple[pd.DataFrame, list[str], list[PowerBIReadyIssue]]:
        """Flatten record-valued fields and serialize unsupported collections."""
        source = dataframe.copy(deep=True)
        source.columns = self._unique_field_names(source.columns)
        output: dict[str, pd.Series] = {}
        changes: list[str] = []
        issues: list[PowerBIReadyIssue] = []

        for column in source.columns:
            series = source[column]
            present = [value for value in series.tolist() if not self._is_missing_scalar(value)]
            has_record = any(isinstance(value, dict) for value in present)
            records_only = bool(present) and all(isinstance(value, dict) for value in present)

            if enabled and records_only:
                records = [value if isinstance(value, dict) else {} for value in series.tolist()]
                nested = pd.json_normalize(records, sep="_")
                for nested_name in sorted(nested.columns, key=str):
                    candidate = self._normalize_name(
                        f"{column}_{nested_name}",
                        fallback=f"{column}_field",
                    )
                    candidate = self._next_name(candidate, output)
                    output[candidate] = pd.Series(
                        nested[nested_name].to_numpy(), index=source.index
                    )
                changes.append(f"[{table_name}] Flattened nested record field '{column}'.")
                continue

            has_collection = any(isinstance(value, (dict, list, tuple)) for value in present)
            if has_record or has_collection:
                serialized = series.map(self._serialize_nested_value).astype("string")
                output[column] = serialized
                code = "nested_serialized" if enabled else "nested_flattening_disabled"
                message = (
                    f"Field '{table_name}.{column}' contained a mixed or collection-valued "
                    "structure and was serialized as deterministic JSON text."
                )
                issues.append(
                    self._issue(
                        code,
                        table_name,
                        column,
                        "warning",
                        message,
                        "Normalize repeating child records into a separate related table.",
                    )
                )
                changes.append(f"[{table_name}] Serialized nested field '{column}' as JSON text.")
                continue

            output[column] = series.copy()

        return pd.DataFrame(output, index=source.index), changes, issues

    def _coerce_field_types(
        self,
        dataframe: pd.DataFrame,
        table_name: str,
    ) -> tuple[pd.DataFrame, list[str]]:
        """Coerce pandas extension types to stable Power BI-compatible fields."""
        output = dataframe.copy(deep=True)
        changes: list[str] = []
        for column in output.columns:
            series = output[column]
            original = str(series.dtype)
            if isinstance(series.dtype, pd.DatetimeTZDtype):
                output[column] = series.dt.tz_convert("UTC").dt.tz_localize(None)
            elif pd.api.types.is_timedelta64_dtype(series):
                output[column] = series.dt.total_seconds().astype("Float64")
            elif isinstance(series.dtype, pd.CategoricalDtype):
                output[column] = series.astype("string")
            elif pd.api.types.is_bool_dtype(series):
                output[column] = series.astype("boolean")
            elif pd.api.types.is_integer_dtype(series):
                output[column] = series.astype("Int64")
            elif pd.api.types.is_float_dtype(series):
                output[column] = series.astype("Float64")
            elif pd.api.types.is_object_dtype(series):
                output[column] = series.astype("string")
            current = str(output[column].dtype)
            if current != original:
                changes.append(
                    f"[{table_name}] Converted field '{column}' from {original} to {current}."
                )
        return output.reset_index(drop=True), changes

    def _build_date_table(
        self,
        tables: dict[str, pd.DataFrame],
        config: PowerBIReadyConfig,
        date_table_name: str,
    ) -> tuple[
        pd.DataFrame | None,
        tuple[PowerBIRelationship, ...],
        list[str],
        list[PowerBIReadyIssue],
    ]:
        """Create one continuous canonical date dimension from configured date fields."""
        references: list[tuple[str, str, pd.Series]] = []
        changes: list[str] = []
        issues: list[PowerBIReadyIssue] = []
        configured = {
            self._normalize_name(table, fallback="table"): tuple(
                self._normalize_name(column, fallback="field") for column in columns
            )
            for table, columns in config.date_columns.items()
        }
        for table_name in configured:
            if table_name not in tables:
                issues.append(
                    self._issue(
                        "missing_date_table_source",
                        table_name,
                        "",
                        "error",
                        f"Configured date source table '{table_name}' was not found.",
                        "Correct the date_columns table name.",
                    )
                )

        for table_name, table in tables.items():
            columns = configured.get(table_name)
            if columns is None:
                if config.date_columns:
                    continue
                columns = tuple(
                    column
                    for column in table.columns
                    if pd.api.types.is_datetime64_any_dtype(table[column])
                )
            for column in columns:
                if column not in table.columns:
                    issues.append(
                        self._issue(
                            "missing_date_field",
                            table_name,
                            column,
                            "error",
                            f"Configured date field '{table_name}.{column}' was not found.",
                            "Correct the date_columns configuration.",
                        )
                    )
                    continue
                values = pd.to_datetime(table[column], errors="coerce")
                invalid = int(table[column].notna().sum() - values.notna().sum())
                if invalid:
                    issues.append(
                        self._issue(
                            "invalid_date_field",
                            table_name,
                            column,
                            "error",
                            f"Date field '{table_name}.{column}' contains "
                            f"{invalid} invalid value(s).",
                            "Correct invalid dates before generating the canonical date table.",
                        )
                    )
                    continue
                relationship_column = column
                normalized_dates = values.dt.normalize()
                if values.notna().any() and not values.dropna().eq(normalized_dates.dropna()).all():
                    relationship_column = self._next_name(f"{column}_date", table)
                    table[relationship_column] = normalized_dates
                    changes.append(
                        f"[{table_name}] Derived date-only field '{relationship_column}' "
                        f"from '{column}'."
                    )
                else:
                    table[column] = normalized_dates
                references.append((table_name, relationship_column, normalized_dates))

        available = [series.dropna() for _, _, series in references if series.notna().any()]
        if not available:
            issues.append(
                self._issue(
                    "date_table_source_missing",
                    date_table_name,
                    "date",
                    "error",
                    "A canonical date table was requested but no valid date values were found.",
                    "Configure at least one valid date field in date_columns.",
                )
            )
            return None, (), changes, issues

        minimum = min(series.min() for series in available)
        maximum = max(series.max() for series in available)
        dates = pd.Series(pd.date_range(minimum, maximum, freq="D"), name="date")
        month_offset = config.fiscal_year_start_month - 1
        fiscal_year = dates.dt.year + (dates.dt.month >= config.fiscal_year_start_month).astype(int)
        if config.fiscal_year_start_month == 1:
            fiscal_year = dates.dt.year
        fiscal_month = ((dates.dt.month - month_offset - 1) % 12) + 1
        date_table = pd.DataFrame(
            {
                "date": dates,
                "date_key": dates.dt.strftime("%Y%m%d").astype("Int64"),
                "year": dates.dt.year.astype("Int64"),
                "quarter": ("Q" + dates.dt.quarter.astype(str)).astype("string"),
                "month_number": dates.dt.month.astype("Int64"),
                "month_name": dates.dt.month_name().astype("string"),
                "year_month": dates.dt.strftime("%Y-%m").astype("string"),
                "day": dates.dt.day.astype("Int64"),
                "day_of_week": dates.dt.day_name().astype("string"),
                "week_of_year": dates.dt.isocalendar().week.astype("Int64"),
                "is_weekend": dates.dt.dayofweek.ge(5).astype("boolean"),
                "fiscal_year": fiscal_year.astype("Int64"),
                "fiscal_month": fiscal_month.astype("Int64"),
            }
        )
        relationships = tuple(
            PowerBIRelationship(
                from_table=table_name,
                from_columns=(column,),
                to_table=date_table_name,
                to_columns=("date",),
                cardinality="many_to_one",
            )
            for table_name, column, _ in references
        )
        changes.append(
            f"[{date_table_name}] Generated canonical date table from "
            f"{minimum.date()} through {maximum.date()}."
        )
        return date_table, relationships, changes, issues

    def _validate_keys(
        self,
        tables: dict[str, pd.DataFrame],
        keys: tuple[PowerBIKey, ...],
    ) -> list[PowerBIReadyIssue]:
        """Validate declared primary or candidate keys."""
        issues: list[PowerBIReadyIssue] = []
        for key in keys:
            table = tables.get(key.table)
            label = ", ".join(key.columns)
            if table is None:
                issues.append(
                    self._issue(
                        "missing_key_table",
                        key.table,
                        label,
                        "error",
                        f"Key table '{key.table}' was not found.",
                        "Correct the PowerBIKey table name.",
                    )
                )
                continue
            missing = [column for column in key.columns if column not in table.columns]
            if missing:
                issues.append(
                    self._issue(
                        "missing_key_field",
                        key.table,
                        label,
                        "error",
                        f"Key field(s) not found in '{key.table}': {', '.join(missing)}.",
                        "Correct the PowerBIKey columns.",
                    )
                )
                continue
            key_values = table.loc[:, list(key.columns)]
            null_rows = int(key_values.isna().any(axis=1).sum())
            duplicate_rows = int(key_values.duplicated(keep=False).sum())
            if null_rows:
                issues.append(
                    self._issue(
                        "null_key",
                        key.table,
                        label,
                        "error",
                        f"Key '{key.table}[{label}]' contains {null_rows} null row(s).",
                        "Populate every key value before loading the model.",
                    )
                )
            if duplicate_rows:
                issues.append(
                    self._issue(
                        "duplicate_key",
                        key.table,
                        label,
                        "error",
                        f"Key '{key.table}[{label}]' contains {duplicate_rows} duplicate row(s).",
                        "Deduplicate the one-side key or declare the correct cardinality.",
                    )
                )
        return issues

    def _validate_relationships(
        self,
        tables: dict[str, pd.DataFrame],
        relationships: tuple[PowerBIRelationship, ...],
    ) -> list[PowerBIReadyIssue]:
        """Validate relationship fields, cardinality, types, and orphan values."""
        issues: list[PowerBIReadyIssue] = []
        for relationship in relationships:
            from_table = tables.get(relationship.from_table)
            to_table = tables.get(relationship.to_table)
            label = f"{relationship.from_table} -> {relationship.to_table}"
            if from_table is None or to_table is None:
                missing = relationship.from_table if from_table is None else relationship.to_table
                issues.append(
                    self._issue(
                        "missing_relationship_table",
                        missing,
                        "",
                        "error",
                        f"Relationship '{label}' references missing table '{missing}'.",
                        "Correct the relationship table names.",
                    )
                )
                continue
            missing_from = [
                column for column in relationship.from_columns if column not in from_table.columns
            ]
            missing_to = [
                column for column in relationship.to_columns if column not in to_table.columns
            ]
            if missing_from or missing_to:
                issues.append(
                    self._issue(
                        "missing_relationship_field",
                        relationship.from_table,
                        ", ".join((*missing_from, *missing_to)),
                        "error",
                        f"Relationship '{label}' references missing field(s): "
                        + ", ".join((*missing_from, *missing_to))
                        + ".",
                        "Correct the relationship column names.",
                    )
                )
                continue

            incompatible = []
            for from_column, to_column in zip(
                relationship.from_columns,
                relationship.to_columns,
            ):
                left = self._type_family(from_table[from_column])
                right = self._type_family(to_table[to_column])
                if left != right:
                    incompatible.append(f"{from_column} ({left}) / {to_column} ({right})")
            if incompatible:
                issues.append(
                    self._issue(
                        "relationship_type_mismatch",
                        relationship.from_table,
                        ", ".join(relationship.from_columns),
                        "error",
                        f"Relationship '{label}' has incompatible field types: "
                        + "; ".join(incompatible)
                        + ".",
                        "Align relationship field types before loading the model.",
                    )
                )

            from_values = from_table.loc[:, list(relationship.from_columns)]
            to_values = to_table.loc[:, list(relationship.to_columns)]
            require_from_unique = relationship.cardinality in {"one_to_many", "one_to_one"}
            require_to_unique = relationship.cardinality in {"many_to_one", "one_to_one"}
            if require_from_unique and from_values.duplicated(keep=False).any():
                issues.append(
                    self._cardinality_issue(relationship, relationship.from_table, "from")
                )
            if require_to_unique and to_values.duplicated(keep=False).any():
                issues.append(self._cardinality_issue(relationship, relationship.to_table, "to"))

            from_keys = self._row_keys(from_values)
            to_keys = self._row_keys(to_values)
            orphan_count = len(from_keys - to_keys)
            if orphan_count:
                issues.append(
                    self._issue(
                        "orphan_relationship_key",
                        relationship.from_table,
                        ", ".join(relationship.from_columns),
                        "warning",
                        f"Relationship '{label}' contains {orphan_count} unmatched key value(s).",
                        "Add matching dimension keys or intentionally handle unknown members.",
                    )
                )
        return issues

    @staticmethod
    def _analysis_issues(table: str, issues: list[object]) -> list[PowerBIReadyIssue]:
        """Project Analysis Ready diagnostics into the Power BI readiness report."""
        return [
            PowerBIReadyIssue(
                code=f"analysis_{issue.code}",
                table=table,
                column=issue.column,
                severity="warning",
                message=issue.message,
                action="Review the Analysis Ready diagnostic before publishing the model.",
            )
            for issue in issues
        ]

    @classmethod
    def _normalize_key(cls, key: PowerBIKey) -> PowerBIKey:
        """Normalize a key declaration with the same rules as data fields."""
        return PowerBIKey(
            table=cls._normalize_name(key.table, fallback="table"),
            columns=tuple(cls._normalize_name(column, fallback="field") for column in key.columns),
        )

    @classmethod
    def _normalize_relationship(
        cls,
        relationship: PowerBIRelationship,
    ) -> PowerBIRelationship:
        """Normalize relationship endpoints with the same rules as data fields."""
        return PowerBIRelationship(
            from_table=cls._normalize_name(relationship.from_table, fallback="table"),
            from_columns=tuple(
                cls._normalize_name(column, fallback="field")
                for column in relationship.from_columns
            ),
            to_table=cls._normalize_name(relationship.to_table, fallback="table"),
            to_columns=tuple(
                cls._normalize_name(column, fallback="field") for column in relationship.to_columns
            ),
            cardinality=relationship.cardinality,
        )

    @staticmethod
    def _serialize_nested_value(value: object) -> object:
        """Return stable JSON text for a nested value while preserving missing values."""
        if value is None:
            return pd.NA
        if isinstance(value, tuple):
            value = list(value)
        if isinstance(value, (dict, list)):
            return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
        return value

    @staticmethod
    def _is_missing_scalar(value: object) -> bool:
        """Return whether a non-collection value is a pandas missing scalar."""
        if isinstance(value, (dict, list, tuple)):
            return False
        missing = pd.isna(value)
        try:
            return bool(missing)
        except (TypeError, ValueError):
            return False

    @classmethod
    def _unique_field_names(cls, columns: object) -> list[str]:
        """Return normalized, non-empty, collision-free field names in source order."""
        names: list[str] = []
        for index, column in enumerate(columns):
            candidate = cls._normalize_name(column, fallback=f"field_{index + 1}")
            names.append(cls._next_name(candidate, names))
        return names

    @staticmethod
    def _normalize_name(value: object, *, fallback: str) -> str:
        """Return a Power BI-safe snake-case table or field name."""
        return ColumnNormalizer.normalize_name(value) or fallback

    @staticmethod
    def _next_name(candidate: str, existing: object) -> str:
        """Return a deterministic suffix when a normalized name already exists."""
        names = set(existing)
        if candidate not in names:
            return candidate
        suffix = 2
        while f"{candidate}_{suffix}" in names:
            suffix += 1
        return f"{candidate}_{suffix}"

    @staticmethod
    def _powerbi_type(series: pd.Series) -> str:
        """Return the closest Power BI field type for a prepared pandas series."""
        if pd.api.types.is_datetime64_any_dtype(series):
            non_null = series.dropna()
            if (
                non_null.empty
                or (
                    non_null.dt.hour.eq(0)
                    & non_null.dt.minute.eq(0)
                    & non_null.dt.second.eq(0)
                    & non_null.dt.microsecond.eq(0)
                ).all()
            ):
                return "Date"
            return "Date/Time"
        if pd.api.types.is_bool_dtype(series):
            return "True/False"
        if pd.api.types.is_integer_dtype(series):
            return "Whole Number"
        if pd.api.types.is_numeric_dtype(series):
            return "Decimal Number"
        return "Text"

    @classmethod
    def _type_family(cls, series: pd.Series) -> str:
        """Return a broad compatibility family for relationship validation."""
        powerbi_type = cls._powerbi_type(series)
        if powerbi_type in {"Whole Number", "Decimal Number"}:
            return "number"
        if powerbi_type in {"Date", "Date/Time"}:
            return "datetime"
        if powerbi_type == "True/False":
            return "boolean"
        return "text"

    @staticmethod
    def _row_keys(values: pd.DataFrame) -> set[tuple[object, ...]]:
        """Return unique non-null composite keys for relationship matching."""
        available = values.loc[~values.isna().any(axis=1)]
        return set(available.itertuples(index=False, name=None))

    @staticmethod
    def _issue(
        code: str,
        table: str,
        column: str,
        severity: str,
        message: str,
        action: str,
    ) -> PowerBIReadyIssue:
        """Construct one immutable Power BI readiness issue."""
        return PowerBIReadyIssue(code, table, column, severity, message, action)

    @classmethod
    def _cardinality_issue(
        cls,
        relationship: PowerBIRelationship,
        table: str,
        side: str,
    ) -> PowerBIReadyIssue:
        """Return a cardinality error for a relationship's expected one side."""
        columns = relationship.from_columns if side == "from" else relationship.to_columns
        return cls._issue(
            "relationship_cardinality",
            table,
            ", ".join(columns),
            "error",
            f"Relationship '{relationship.from_table} -> {relationship.to_table}' expects "
            f"'{table}' to be unique for {relationship.cardinality} cardinality.",
            "Deduplicate the one side or declare the correct cardinality.",
        )

    @staticmethod
    def _readiness_score(issues: list[PowerBIReadyIssue]) -> float:
        """Calculate a transparent readiness score from diagnostic severity."""
        warnings = sum(1 for issue in issues if issue.severity == "warning")
        errors = sum(1 for issue in issues if issue.severity == "error")
        return round(max(0.0, 100.0 - min(warnings * 3.0, 30.0) - errors * 25.0), 2)
