"""
CSV data source.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from easydatafix.datasources.base import DataSource


class CSVDataSource(DataSource):
    """
    Loads ``.csv`` files via :func:`pandas.read_csv`.
    """

    name = "csv"
    extensions = (".csv",)

    def can_load(self, source) -> bool:
        return (
            isinstance(source, Path)
            and source.suffix.lower() in self.extensions
        )

    def load(self, source) -> pd.DataFrame:
        return pd.read_csv(source)
