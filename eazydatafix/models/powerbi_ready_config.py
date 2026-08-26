from dataclasses import dataclass, field

from eazydatafix.models.analysis_ready_config import AnalysisReadyConfig


@dataclass(frozen=True, slots=True)
class PowerBIKey:
    """Declare a candidate key that must be unique and non-null."""

    table: str
    columns: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate the table and composite-key declaration."""
        if not isinstance(self.table, str) or not self.table.strip():
            raise ValueError("Power BI key table must be a non-empty string.")
        if not isinstance(self.columns, tuple) or not self.columns:
            raise ValueError("Power BI key columns must be a non-empty tuple.")
        if any(not isinstance(column, str) or not column.strip() for column in self.columns):
            raise ValueError("Power BI key columns must contain non-empty strings.")


@dataclass(frozen=True, slots=True)
class PowerBIRelationship:
    """Declare an expected relationship between two Power BI model tables."""

    from_table: str
    from_columns: tuple[str, ...]
    to_table: str
    to_columns: tuple[str, ...]
    cardinality: str = "many_to_one"

    def __post_init__(self) -> None:
        """Validate relationship endpoints and supported cardinality."""
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (self.from_table, self.to_table)
        ):
            raise ValueError("Relationship table names must be non-empty strings.")
        for name, columns in (
            ("from_columns", self.from_columns),
            ("to_columns", self.to_columns),
        ):
            if not isinstance(columns, tuple) or not columns:
                raise ValueError(f"{name} must be a non-empty tuple.")
            if any(not isinstance(column, str) or not column.strip() for column in columns):
                raise ValueError(f"{name} must contain non-empty strings.")
        if len(self.from_columns) != len(self.to_columns):
            raise ValueError("Relationship endpoints must contain the same number of columns.")
        if self.cardinality not in {
            "many_to_one",
            "one_to_many",
            "one_to_one",
            "many_to_many",
        }:
            raise ValueError(
                "cardinality must be one of: many_to_one, one_to_many, " "one_to_one, many_to_many."
            )


@dataclass(slots=True)
class PowerBIReadyConfig:
    """Configure deterministic preparation for a Power BI semantic model."""

    analysis_ready_config: AnalysisReadyConfig = field(default_factory=AnalysisReadyConfig)
    table_name: str = "data"
    keys: tuple[PowerBIKey, ...] = ()
    relationships: tuple[PowerBIRelationship, ...] = ()
    flatten_nested: bool = True
    generate_date_table: bool = False
    date_columns: dict[str, tuple[str, ...]] = field(default_factory=dict)
    date_table_name: str = "date"
    fiscal_year_start_month: int = 1
    minimum_readiness_score: float = 80.0

    def __post_init__(self) -> None:
        """Validate BI transformation and model-contract controls."""
        if not isinstance(self.analysis_ready_config, AnalysisReadyConfig):
            raise TypeError("analysis_ready_config must be an AnalysisReadyConfig instance.")
        if self.analysis_ready_config.fix_config.dry_run:
            raise ValueError("Power BI Ready does not accept a dry-run FixConfig.")
        for name in ("table_name", "date_table_name"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
        if not isinstance(self.keys, tuple) or any(
            not isinstance(key, PowerBIKey) for key in self.keys
        ):
            raise TypeError("keys must be a tuple of PowerBIKey values.")
        if not isinstance(self.relationships, tuple) or any(
            not isinstance(relationship, PowerBIRelationship) for relationship in self.relationships
        ):
            raise TypeError("relationships must be a tuple of PowerBIRelationship values.")
        if not isinstance(self.flatten_nested, bool):
            raise TypeError("flatten_nested must be a boolean.")
        if not isinstance(self.generate_date_table, bool):
            raise TypeError("generate_date_table must be a boolean.")
        if any(
            not isinstance(table, str)
            or not isinstance(columns, tuple)
            or any(not isinstance(column, str) for column in columns)
            for table, columns in self.date_columns.items()
        ):
            raise TypeError("date_columns must map table names to tuples of column names.")
        if (
            not isinstance(self.fiscal_year_start_month, int)
            or isinstance(self.fiscal_year_start_month, bool)
            or not 1 <= self.fiscal_year_start_month <= 12
        ):
            raise ValueError("fiscal_year_start_month must be an integer from 1 to 12.")
        if not isinstance(self.minimum_readiness_score, float) or not (
            0.0 <= self.minimum_readiness_score <= 100.0
        ):
            raise ValueError("minimum_readiness_score must be a float between 0 and 100.")
