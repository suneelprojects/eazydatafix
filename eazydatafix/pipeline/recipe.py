"""Versioned, declarative recipes without executable configuration."""

from __future__ import annotations

import json
import math
import types
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any, Union, get_args, get_origin, get_type_hints

from eazydatafix.fix.strategies.factory import StrategyFactory
from eazydatafix.models.data_contract import DataContract, QualityRule
from eazydatafix.models.fix_config import FixConfig
from eazydatafix.models.ml_ready_config import MLReadyConfig
from eazydatafix.models.powerbi_ready_config import PowerBIReadyConfig
from eazydatafix.models.prepare_config import PrepareConfig


def _decode(annotation: Any, value: Any, path: str) -> Any:
    """Strictly decode JSON/YAML values using the declared dataclass schema."""
    origin = get_origin(annotation)
    arguments = get_args(annotation)
    if origin in {Union, types.UnionType}:
        for option in arguments:
            try:
                return _decode(option, value, path)
            except (TypeError, ValueError):
                pass
        raise ValueError(f"Invalid value at {path}.")
    if annotation is type(None):
        if value is not None:
            raise ValueError(f"{path} must be null.")
        return None
    if annotation is Any:
        return value
    if is_dataclass(annotation):
        if not isinstance(value, dict):
            raise ValueError(f"{path} must be an object.")
        known = {item.name for item in fields(annotation)}
        unknown = set(value) - known
        if unknown:
            raise ValueError(f"Unknown fields at {path}: {', '.join(sorted(unknown))}.")
        hints = get_type_hints(annotation)
        return annotation(
            **{key: _decode(hints[key], item, f"{path}.{key}") for key, item in value.items()}
        )
    if origin is tuple:
        if not isinstance(value, (list, tuple)):
            raise ValueError(f"{path} must be an array.")
        return tuple(_decode(arguments[0], item, f"{path}[{i}]") for i, item in enumerate(value))
    if origin is dict:
        if not isinstance(value, dict):
            raise ValueError(f"{path} must be an object.")
        return {
            _decode(arguments[0], key, path): _decode(arguments[1], item, f"{path}.{key}")
            for key, item in value.items()
        }
    if annotation is float:
        if (
            isinstance(value, bool)
            or not isinstance(value, (float, int))
            or not math.isfinite(value)
        ):
            raise ValueError(f"{path} must be a finite number.")
        return float(value)
    if type(value) is not annotation:
        raise ValueError(f"{path} must be {annotation.__name__}.")
    return value


@dataclass(frozen=True, slots=True)
class ColumnRule:
    """Declare a column type, literal cleanup, and explicit conversion failure policy."""

    dtype: str | None = None
    on_error: str = "reject"
    required: bool = True
    date_format: str | None = None
    decimal_separator: str = "."
    thousands_separator: str | None = ","
    currency_symbols: tuple[str, ...] = ()
    percentage: bool = False
    category_mapping: dict[str, str] = field(default_factory=dict)
    missing_markers: tuple[str, ...] = ()
    fill_value: str | float | int | bool | None = None

    def __post_init__(self) -> None:
        """Reject ambiguous type rules and mappings that cannot be replayed idempotently."""
        if self.dtype not in {
            None,
            "string",
            "integer",
            "number",
            "boolean",
            "datetime",
            "category",
        }:
            raise ValueError(
                "dtype must be string, integer, number, boolean, datetime or category."
            )
        if self.on_error not in {"preserve", "reject", "quarantine"}:
            raise ValueError("on_error must be preserve, reject or quarantine.")
        if not isinstance(self.required, bool) or not isinstance(self.percentage, bool):
            raise TypeError("required and percentage must be booleans.")
        if self.dtype == "datetime" and not self.date_format:
            raise ValueError("datetime rules require date_format, for example '%d/%m/%Y'.")
        if self.date_format is not None and not isinstance(self.date_format, str):
            raise TypeError("date_format must be a string or None.")
        if self.decimal_separator not in {".", ","}:
            raise ValueError("decimal_separator must be '.' or ','.")
        if self.thousands_separator not in {None, ".", ",", " "}:
            raise ValueError("Unsupported thousands_separator.")
        if self.thousands_separator == self.decimal_separator:
            raise ValueError("Decimal and thousands separators must differ.")
        for values in (self.currency_symbols, self.missing_markers):
            if not isinstance(values, tuple) or any(
                not isinstance(x, str) or not x for x in values
            ):
                raise TypeError("currency_symbols and missing_markers must be tuples of tokens.")
        if not isinstance(self.category_mapping, dict) or any(
            not isinstance(k, str) or not isinstance(v, str)
            for k, v in self.category_mapping.items()
        ):
            raise TypeError("category_mapping must map strings to strings.")
        if any(self.category_mapping.get(v, v) != v for v in self.category_mapping.values()):
            raise ValueError("category_mapping must not contain chains or cycles.")
        if self.fill_value is not None and type(self.fill_value) not in {str, float, int, bool}:
            raise TypeError("fill_value must be a JSON scalar.")
        if isinstance(self.fill_value, float) and not math.isfinite(self.fill_value):
            raise ValueError("fill_value must be finite.")
        if self.percentage and self.dtype != "number":
            raise ValueError("percentage requires dtype='number'.")


def _safe_fix() -> FixConfig:
    return FixConfig(
        missing_value_strategy="keep",
        convert_data_types=False,
        remove_empty_columns=False,
        remove_empty_rows=False,
    )


@dataclass(frozen=True, slots=True)
class PipelineRecipe:
    """Persist preparation rules and one of the three readiness workflows."""

    name: str = "data_preparation"
    recipe_format_version: int = 1
    workflow: str = "analysis_ready"
    columns: dict[str, ColumnRule] = field(default_factory=dict)
    table_columns: dict[str, dict[str, ColumnRule]] = field(default_factory=dict)
    fix_config: FixConfig = field(default_factory=_safe_fix)
    prepare_config: PrepareConfig = field(default_factory=lambda: PrepareConfig(infer_types=False))
    contract: DataContract | None = None
    quality_rules: tuple[QualityRule, ...] = ()
    target: str | None = None
    ml_config: MLReadyConfig = field(default_factory=MLReadyConfig)
    powerbi_config: PowerBIReadyConfig = field(default_factory=PowerBIReadyConfig)
    audit_sample_size: int = 5
    detailed_audit: bool = False

    def __post_init__(self) -> None:
        """Validate recipe structure, defaults and leakage constraints."""
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Recipe name must be a non-empty string.")
        if type(self.recipe_format_version) is not int or self.recipe_format_version != 1:
            raise ValueError("Unsupported recipe_format_version; expected 1.")
        if self.workflow not in {"analysis_ready", "ml_ready", "powerbi_ready"}:
            raise ValueError("Unsupported recipe workflow.")
        if not isinstance(self.fix_config, FixConfig) or self.fix_config.dry_run:
            raise ValueError("Recipes require a non-dry-run FixConfig; use Pipeline.preview().")
        if not isinstance(self.prepare_config, PrepareConfig):
            raise TypeError("prepare_config must be PrepareConfig.")
        StrategyFactory.create(self.fix_config.missing_value_strategy)
        for rule in self.fix_config.column_rules.values():
            if rule.missing_value_strategy is not None:
                StrategyFactory.create(rule.missing_value_strategy)
        if not isinstance(self.ml_config, MLReadyConfig):
            raise TypeError("ml_config must be MLReadyConfig.")
        if not isinstance(self.powerbi_config, PowerBIReadyConfig):
            raise TypeError("powerbi_config must be PowerBIReadyConfig.")
        if self.contract is not None and not isinstance(self.contract, DataContract):
            raise TypeError("contract must be DataContract or None.")
        if not isinstance(self.quality_rules, tuple) or any(
            not isinstance(rule, QualityRule) for rule in self.quality_rules
        ):
            raise TypeError("quality_rules must be a tuple of QualityRule values.")
        if not isinstance(self.table_columns, dict):
            raise TypeError("table_columns must be a mapping.")
        for table, rules in [("data", self.columns), *self.table_columns.items()]:
            if not isinstance(table, str) or not table or not isinstance(rules, dict):
                raise TypeError("table_columns must map table names to column-rule mappings.")
            if any(
                not isinstance(k, str) or not k or not isinstance(v, ColumnRule)
                for k, v in rules.items()
            ):
                raise TypeError("Column names must map to ColumnRule values.")
        if self.table_columns and self.workflow != "powerbi_ready":
            raise ValueError("table_columns is only supported for powerbi_ready recipes.")
        if type(self.audit_sample_size) is not int or not 0 <= self.audit_sample_size <= 100:
            raise ValueError("audit_sample_size must be an integer from 0 to 100.")
        if not isinstance(self.detailed_audit, bool):
            raise TypeError("detailed_audit must be a boolean.")
        if self.workflow == "ml_ready":
            if not isinstance(self.target, str) or not self.target:
                raise ValueError("ml_ready recipes require an explicit target.")
            if self.fix_config.missing_value_strategy != "keep" or any(
                rule.missing_value_strategy not in {None, "keep"}
                for rule in self.fix_config.column_rules.values()
            ):
                raise ValueError(
                    "ML recipes must keep missing values for training-only imputation."
                )
            if self.prepare_config.outlier_action != "none":
                raise ValueError("ML recipes cannot fit outlier rules before splitting.")
            if self.prepare_config.infer_types or self.fix_config.convert_data_types:
                raise ValueError("ML recipes require explicit types, not full-dataset inference.")
            if any(rule.fill_value is not None for rule in self.columns.values()):
                raise ValueError("ML recipes must fit missing-value imputation after splitting.")

    def to_dict(self) -> dict[str, Any]:
        """Return a detached JSON-compatible recipe, without credentials or code."""
        return json.loads(json.dumps(asdict(self), allow_nan=False))

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> PipelineRecipe:
        """Load a recipe with strict unknown-field and type validation."""
        return _decode(cls, payload, "recipe")

    def save(self, path: str | Path) -> None:
        """Save versioned JSON or YAML; YAML requires the optional yaml extra."""
        destination = Path(path)
        if destination.suffix.lower() == ".json":
            text = json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"
        elif destination.suffix.lower() in {".yaml", ".yml"}:
            try:
                import yaml
            except ImportError as error:
                raise ImportError("Install YAML support with eazydatafix[yaml].") from error
            text = yaml.safe_dump(self.to_dict(), sort_keys=True, allow_unicode=True)
        else:
            raise ValueError("Recipe filename must end in .json, .yaml or .yml.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> PipelineRecipe:
        """Load a JSON/YAML recipe without executing custom code."""
        source = Path(path)
        text = source.read_text(encoding="utf-8")
        if source.suffix.lower() == ".json":
            payload = json.loads(text)
        elif source.suffix.lower() in {".yaml", ".yml"}:
            try:
                import yaml
            except ImportError as error:
                raise ImportError("Install YAML support with eazydatafix[yaml].") from error
            payload = yaml.safe_load(text)
        else:
            raise ValueError("Recipe filename must end in .json, .yaml or .yml.")
        return cls.from_dict(payload)
