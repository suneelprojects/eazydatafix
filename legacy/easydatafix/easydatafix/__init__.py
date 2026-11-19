"""Final compatibility release for the retired PyPI name ``easydatafix``."""

from __future__ import annotations

import warnings
from typing import Any

import eazydatafix as _eazydatafix

warnings.filterwarnings(
    "default",
    message=r"easydatafix is deprecated\..*",
    category=DeprecationWarning,
    module=r"easydatafix",
)
warnings.warn(
    "easydatafix is deprecated. This 0.3.0 release only forwards to eazydatafix "
    "and will not be updated. Install and import eazydatafix instead: "
    "pip install eazydatafix",
    DeprecationWarning,
    stacklevel=1,
)

__version__ = "0.3.0"
__eazydatafix_version__ = _eazydatafix.__version__
__all__ = ["__version__", "__eazydatafix_version__", *_eazydatafix.__all__]


def __getattr__(name: str) -> Any:
    """Forward attribute access to the installed eazydatafix package."""
    return getattr(_eazydatafix, name)


def __dir__() -> list[str]:
    """Advertise the forwarded public names."""
    return sorted(set(__all__) | set(globals()))
