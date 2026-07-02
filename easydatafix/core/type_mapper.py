from easydatafix.enums.data_type import DataType


class TypeMapper:
    """
    Converts backend-specific data types into Easy Data Fix data types.
    """

    _PANDAS_MAPPING = {
        # Integer
        "int8": DataType.INTEGER,
        "int16": DataType.INTEGER,
        "int32": DataType.INTEGER,
        "int64": DataType.INTEGER,
        # Decimal
        "float16": DataType.DECIMAL,
        "float32": DataType.DECIMAL,
        "float64": DataType.DECIMAL,
        # Text
        "object": DataType.TEXT,
        "string": DataType.TEXT,
        "str": DataType.TEXT,
        # Boolean
        "bool": DataType.BOOLEAN,
        # Date & Time
        "datetime64[ns]": DataType.DATETIME,
        "timedelta64[ns]": DataType.DURATION,
        # Category
        "category": DataType.CATEGORY,
    }

    @classmethod
    def from_pandas(cls, dtype: str) -> DataType:
        return cls._PANDAS_MAPPING.get(dtype, DataType.UNKNOWN)
