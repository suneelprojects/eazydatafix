"""
DataFrame data source.
"""

from __future__ import annotations

import pandas as pd

from easydatafix.datasources.base import DataSource


class DataFrameDataSource(DataSource):
    """
    Handles pandas DataFrames passed directly to the loader.
    """

    name = "dataframe"

    def can_load(self, source) -> bool:
        return isinstance(source, pd.DataFrame)

    def load(self, source) -> pd.DataFrame:
        return source.copy()
