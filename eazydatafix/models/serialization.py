import math
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any


def to_json_compatible(value: Any) -> Any:
    """
    Convert dataclasses and common scientific values to JSON-ready values.

    Args:
        value: The value to convert.

    Returns:
        A recursively converted value containing JSON-compatible structures.
    """
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: to_json_compatible(getattr(value, field.name)) for field in fields(value)
        }

    if isinstance(value, dict):
        return {str(key): to_json_compatible(item) for key, item in value.items()}

    if isinstance(value, (list, tuple)):
        return [to_json_compatible(item) for item in value]

    if isinstance(value, Enum):
        return to_json_compatible(value.value)

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, float) and not math.isfinite(value):
        return None

    item = getattr(value, "item", None)

    if callable(item):
        return to_json_compatible(item())

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    return str(value)
