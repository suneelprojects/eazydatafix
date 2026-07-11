"""
JSON data source.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from easydatafix.datasources.base import DataSource


class JSONDataSource(DataSource):
    """
    Loads ``.json`` files via :func:`pandas.read_json`.
    """

    name = "json"
    extensions = (".json",)

    def can_load(self, source) -> bool:
        return (
            isinstance(source, Path)
            and source.suffix.lower() in self.extensions
        )

    def load(self, source) -> pd.DataFrame:
        return pd.read_json(source)
