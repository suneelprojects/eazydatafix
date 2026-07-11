"""
Backward-compatible re-export of :class:`DatasetLoader`.

The dataset loading logic now lives in :mod:`easydatafix.datasources`.
This module is kept so existing imports continue to work:

    from easydatafix.core.dataset_loader import DatasetLoader
"""

from easydatafix.datasources.loader import DatasetLoader

__all__ = ["DatasetLoader"]
