"""
Base contract for data sources.

A data source is a small object that knows how to recognise a particular
kind of input (a file path with a given extension, an in-memory object,
etc.) and load it into a :class:`pandas.DataFrame`.

The base class defined here is intentionally lightweight: it does not use
``abc.ABC`` and does not enforce anything at import time. Concrete data
sources simply implement ``can_load`` and ``load``.
"""

from __future__ import annotations

import pandas as pd


class DataSource:
    """
    Base class for all data sources.

    Concrete subclasses must implement:

    - ``can_load(source)`` -> bool
        Return ``True`` if this data source can handle ``source``.

    - ``load(source)`` -> pandas.DataFrame
        Load ``source`` into a DataFrame.

    The optional ``name`` attribute is used purely for diagnostics.
    """

    #: Human-readable identifier for the data source.
    name: str = "datasource"

    def can_load(self, source) -> bool:
        """
        Return ``True`` if this data source can load ``source``.
        """
        return False

    def load(self, source) -> pd.DataFrame:
        """
        Load ``source`` into a pandas DataFrame.
        """
        raise NotImplementedError
