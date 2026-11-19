"""Helpers for optional install extras."""

from __future__ import annotations

import importlib
from types import ModuleType


class OptionalDependencyError(ImportError):
    """Raised when a called feature needs an optional install extra."""


def require_extra(module_name: str, extra: str, feature: str) -> ModuleType:
    """Import ``module_name`` or raise a message that names the extra to install.

    Args:
        module_name: Module that provides the optional feature.
        extra: Extra name used in ``eazydatafix[<extra>]``.
        feature: Short description of the caller-facing capability.

    Returns:
        The imported module.

    Raises:
        OptionalDependencyError: When the module is not installed. The message
            includes the ``pip install "eazydatafix[<extra>]"`` command.
    """
    try:
        return importlib.import_module(module_name)
    except ImportError as exc:
        raise OptionalDependencyError(
            f"{feature} requires the optional '{extra}' extra ({module_name}). "
            f'Install it with: pip install "eazydatafix[{extra}]"'
        ) from exc
