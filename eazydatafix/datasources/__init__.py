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

from eazydatafix.datasources.base import DataSource
from eazydatafix.datasources.csv import CSVDataSource
from eazydatafix.datasources.dataframe import DataFrameDataSource
from eazydatafix.datasources.excel import ExcelDataSource
from eazydatafix.datasources.json import JSONDataSource
from eazydatafix.datasources.loader import (
    DatasetLoader,
    build_default_registry,
    default_registry,
)
from eazydatafix.datasources.parquet import ParquetDataSource
from eazydatafix.datasources.registry import DataSourceRegistry

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
