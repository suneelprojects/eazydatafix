from dataclasses import dataclass, field

from eazydatafix.models.column_cleaning_rule import ColumnCleaningRule


@dataclass(slots=True)
class FixConfig:
    """
    Configuration for automatic data cleaning.
    """

    missing_value_strategy: str = "smart"
    missing_markers: tuple[str, ...] = ("", "na", "n/a", "nan", "none", "null")
    column_rules: dict[str, ColumnCleaningRule] = field(default_factory=dict)
    dry_run: bool = False

    remove_duplicates: bool = True
    remove_empty_rows: bool = True
    remove_empty_columns: bool = True

    trim_whitespace: bool = True
    normalize_column_names: bool = True
    convert_data_types: bool = True

    def __post_init__(self) -> None:
        """Validate deterministic cleaning options and column-level overrides."""
        if not isinstance(self.missing_value_strategy, str):
            raise TypeError("missing_value_strategy must be a string.")
        if not isinstance(self.dry_run, bool):
            raise TypeError("dry_run must be a boolean.")
        if any(not isinstance(marker, str) for marker in self.missing_markers):
            raise TypeError("missing_markers must contain only strings.")
        if any(
            not isinstance(column, str) or not isinstance(rule, ColumnCleaningRule)
            for column, rule in self.column_rules.items()
        ):
            raise TypeError("column_rules must map column names to ColumnCleaningRule values.")

    def markers_for(self, column: str) -> tuple[str, ...]:
        """Return the configured markers for a normalized column."""
        rule = self.column_rules.get(column)
        return (
            self.missing_markers
            if rule is None or rule.missing_markers is None
            else rule.missing_markers
        )

    def should_trim(self, column: str) -> bool:
        """Return whether whitespace trimming is enabled for a normalized column."""
        rule = self.column_rules.get(column)
        return (
            self.trim_whitespace
            if rule is None or rule.trim_whitespace is None
            else rule.trim_whitespace
        )
