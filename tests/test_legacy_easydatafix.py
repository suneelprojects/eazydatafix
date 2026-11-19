"""The unpublished easydatafix shim warns and forwards to eazydatafix."""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import eazydatafix as edf

_LEGACY_ROOT = Path(__file__).resolve().parents[1] / "legacy" / "easydatafix"


def test_legacy_package_metadata_points_at_eazydatafix() -> None:
    text = (_LEGACY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert '\nname = "easydatafix"\n' in text
    assert '\nversion = "0.3.0"\n' in text
    assert '"eazydatafix>=2.0.0,<3"' in text


def test_legacy_import_warns_and_forwards_public_api() -> None:
    sys.path.insert(0, str(_LEGACY_ROOT))
    sys.modules.pop("easydatafix", None)
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            import easydatafix

            assert easydatafix.__version__ == "0.3.0"
            assert easydatafix.__eazydatafix_version__ == edf.__version__
            assert easydatafix.PipelineRecipe is edf.PipelineRecipe
            assert easydatafix.fix is edf.fix
            assert any(
                issubclass(item.category, DeprecationWarning) and "eazydatafix" in str(item.message)
                for item in caught
            )
    finally:
        sys.path.remove(str(_LEGACY_ROOT))
        sys.modules.pop("easydatafix", None)
