from enum import Enum


class DataType(str, Enum):
    """
    Framework data types used throughout EazyDataFix.
    """

    INTEGER = "Integer"
    DECIMAL = "Decimal"
    TEXT = "Text"
    BOOLEAN = "Boolean"
    DATE = "Date"
    DATETIME = "DateTime"
    CATEGORY = "Category"
    DURATION = "Duration"
    UNKNOWN = "Unknown"
