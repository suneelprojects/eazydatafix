"""Core paths stay importable when plotting and PDF libraries are absent."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest

import eazydatafix as edf
from eazydatafix._optional import OptionalDependencyError
from eazydatafix.reporting.agentic_eda.charts.base import ChartHandler
from eazydatafix.reporting.agentic_eda.charts.registry import ChartRegistry


def _toml_array(text: str, name: str) -> str:
    marker = f"{name} = ["
    return text.split(marker, 1)[1].split("]", 1)[0]


def test_reports_extra_is_optional_and_included_in_all() -> None:
    project_root = Path(__file__).resolve().parents[1]
    text = (project_root / "pyproject.toml").read_text(encoding="utf-8")
    dependencies = _toml_array(text, "dependencies")
    reports = _toml_array(text, "reports")

    assert "matplotlib" not in dependencies
    assert "reportlab" not in dependencies
    assert "matplotlib>=" in reports
    assert "reportlab>=" in reports
    assert '"eazydatafix[ml,openai,parquet,reports,yaml]"' in text


def test_chart_registry_does_not_swallow_missing_reports_extra(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _missing_matplotlib() -> None:
        raise OptionalDependencyError(
            "PNG charts require the optional 'reports' extra (matplotlib). "
            'Install it with: pip install "eazydatafix[reports]"'
        )

    monkeypatch.setattr(ChartHandler, "pyplot", staticmethod(_missing_matplotlib))

    class _Chart(ChartHandler):
        type = "missing_value_chart"

        def generate(self, recommendation, context, output_path) -> None:
            self.pyplot()

    workflow = SimpleNamespace(
        recommended_visualisations=[
            edf.VisualisationRecommendation(
                type="missing_value_chart",
                target_columns=["salary"],
                reason="Missing values are present.",
                priority="high",
                source_step="missing_value_analysis",
                prerequisites=[],
            )
        ]
    )
    registry = ChartRegistry(handlers=[_Chart()])

    with pytest.raises(OptionalDependencyError, match=r"eazydatafix\[reports\]"):
        registry.generate(workflow, context=None, output_directory=tmp_path)


def test_core_import_recipe_and_reporting_error_without_plot_or_pdf_libraries(
    tmp_path: Path,
) -> None:
    script = tmp_path / "check_core_without_reports.py"
    script.write_text(
        textwrap.dedent("""
            import importlib.machinery
            import sys

            class _BlockedLoader:
                def create_module(self, spec):
                    return None

                def exec_module(self, module):
                    raise ImportError(f"{module.__name__} is blocked for this test")

            class _BlockReports:
                def find_spec(self, fullname, path, target=None):
                    root = fullname.split(".", 1)[0]
                    if root in {"matplotlib", "reportlab"}:
                        return importlib.machinery.ModuleSpec(fullname, _BlockedLoader())
                    return None

            sys.meta_path.insert(0, _BlockReports())

            import pandas as pd

            import eazydatafix as edf
            import eazydatafix.reporting as reporting

            frame = pd.DataFrame(
                {
                    "customer_id": ["001", "002"],
                    "amount": ["₹10", "₹20"],
                    "order_date": ["01/02/2025", "02/02/2025"],
                }
            )
            recipe = edf.PipelineRecipe(
                name="tiny",
                columns={
                    "customer_id": edf.ColumnRule(dtype="string"),
                    "amount": edf.ColumnRule(
                        dtype="number",
                        currency_symbols=("₹",),
                    ),
                    "order_date": edf.ColumnRule(
                        dtype="datetime",
                        date_format="%d/%m/%Y",
                    ),
                },
            )
            pipeline = edf.Pipeline(recipe)
            plan = pipeline.preview(frame)
            result = pipeline.apply(frame, plan)
            assert result.is_ready
            assert result.dataset["customer_id"].tolist() == ["001", "002"]

            profile = edf.profile(frame)
            assert profile.rows == 2
            fixed = edf.fix(frame)
            assert list(fixed.dataset.columns)

            assert reporting.PdfReport is not None
            assert "matplotlib" not in sys.modules
            assert "reportlab" not in sys.modules

            report = edf.assess(frame)
            try:
                report.to_pdf("should-not-write.pdf")
            except ImportError as exc:
                message = str(exc)
                assert "eazydatafix[reports]" in message
                assert "reportlab" in message
            else:
                raise SystemExit("to_pdf did not raise")

            from eazydatafix.reporting.agentic_eda.charts.base import ChartHandler

            try:
                ChartHandler.pyplot()
            except ImportError as exc:
                message = str(exc)
                assert "eazydatafix[reports]" in message
                assert "matplotlib" in message
            else:
                raise SystemExit("pyplot did not raise")
            """),
        encoding="utf-8",
    )
    completed = subprocess.run(
        [sys.executable, str(script)],
        check=False,
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert completed.returncode == 0, completed.stdout + "\n" + completed.stderr
