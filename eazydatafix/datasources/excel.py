"""
Excel data source.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from eazydatafix.datasources.base import DataSource


class ExcelDataSource(DataSource):
    """
    Loads ``.xlsx`` / ``.xls`` files via :func:`pandas.read_excel`.
    """

    name = "excel"
    extensions = (".xlsx", ".xls")

    def can_load(self, source) -> bool:
        return (
            isinstance(source, Path)
            and source.suffix.lower() in self.extensions
        )

    def load(self, source) -> pd.DataFrame:
        return pd.read_excel(source)
