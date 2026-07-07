from pathlib import Path

import pytest


@pytest.fixture
def data_dir() -> Path:
    """
    Returns the directory containing test datasets.
    """
    return Path(__file__).parent / "data"
