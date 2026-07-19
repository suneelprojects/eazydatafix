"""
Parquet data source.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from eazydatafix.datasources.base import DataSource
from eazydatafix.exceptions import InvalidDatasetError


class ParquetDataSource(DataSource):
    """
    Loads ``.parquet`` files via :func:`pandas.read_parquet`.

    Requires ``pyarrow`` (recommended) or ``fastparquet`` to be installed.
    """

    name = "parquet"
    extensions = (".parquet",)

    def can_load(self, source) -> bool:
        return (
            isinstance(source, Path)
            and source.suffix.lower() in self.extensions
        )

    def load(self, source) -> pd.DataFrame:
        try:
            return pd.read_parquet(source)

        except ImportError as exc:
            raise InvalidDatasetError(
                "Reading Parquet files requires 'pyarrow' (recommended) "
                "or 'fastparquet'. Install with: "
                "pip install eazydatafix[parquet]  "
                "-- or -- pip install pyarrow"
            ) from exc
