from dataclasses import dataclass


@dataclass(slots=True)
class FixConfig:
    """
    Configuration for automatic data cleaning.
    """

    missing_value_strategy: str = "smart"
    remove_duplicates: bool = True
    remove_empty_rows: bool = True
    remove_empty_columns: bool = True
    trim_whitespace: bool = True
    normalize_column_names: bool = False
