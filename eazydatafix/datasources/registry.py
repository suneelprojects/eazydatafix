"""
Data source registry.

The registry keeps an ordered list of :class:`DataSource` instances and
resolves the first one whose ``can_load`` returns ``True`` for a given
input.
"""

from __future__ import annotations

from eazydatafix.datasources.base import DataSource
from eazydatafix.exceptions import InvalidDatasetError


class DataSourceRegistry:
    """
    Ordered registry of data sources.
    """

    def __init__(self) -> None:
        self._sources: list[DataSource] = []

    def register(self, data_source: DataSource) -> None:
        """
        Register a data source. Sources registered first take priority.
        """
        self._sources.append(data_source)

    def sources(self) -> list[DataSource]:
        """
        Return the list of registered data sources.
        """
        return list(self._sources)

    def resolve(self, source) -> DataSource:
        """
        Return the first registered data source that can load ``source``.

        Raises:
            InvalidDatasetError: If no registered data source can handle
                the given input.
        """
        for data_source in self._sources:
            if data_source.can_load(source):
                return data_source

        raise InvalidDatasetError(
            f"No data source available for: {source!r}"
        )
