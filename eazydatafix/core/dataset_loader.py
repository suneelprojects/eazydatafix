"""
Backward-compatible re-export of :class:`DatasetLoader`.

The dataset loading logic now lives in :mod:`eazydatafix.datasources`.
This module is kept so existing imports continue to work:

    from eazydatafix.core.dataset_loader import DatasetLoader
"""

from eazydatafix.datasources.loader import DatasetLoader

__all__ = ["DatasetLoader"]
