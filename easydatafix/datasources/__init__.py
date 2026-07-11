"""
Data source architecture for EasyDataFix.

Public exports:

- :class:`DataSource`             -- base class for all data sources
- :class:`DataSourceRegistry`     -- ordered registry of data sources
- :class:`DatasetLoader`          -- façade used by the assessment / fix engines
- :data:`default_registry`        -- registry pre-populated with built-in sources
- :class:`DataFrameDataSource`
- :class:`CSVDataSource`
- :class:`ExcelDataSource`
- :class:`JSONDataSource`
- :class:`ParquetDataSource`
"""

from easydatafix.datasources.base import DataSource
from easydatafix.datasources.csv import CSVDataSource
from easydatafix.datasources.dataframe import DataFrameDataSource
from easydatafix.datasources.excel import ExcelDataSource
from easydatafix.datasources.json import JSONDataSource
from easydatafix.datasources.loader import (
    DatasetLoader,
    build_default_registry,
    default_registry,
)
from easydatafix.datasources.parquet import ParquetDataSource
from easydatafix.datasources.registry import DataSourceRegistry

__all__ = [
    "DataSource",
    "DataSourceRegistry",
    "DatasetLoader",
    "build_default_registry",
    "default_registry",
    "DataFrameDataSource",
    "CSVDataSource",
    "ExcelDataSource",
    "JSONDataSource",
    "ParquetDataSource",
]
