"""Discoverability examples: the notebook outline and the Power BI script."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

_EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "power_bi_ready"


def test_power_bi_ready_example_exports_typed_tables_and_change_log(tmp_path: Path) -> None:
    completed = subprocess.run(
        [sys.executable, str(_EXAMPLE / "prepare.py"), "--output", str(tmp_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr

    sales_path = tmp_path / "powerbi_ready_sales.csv"
    date_path = tmp_path / "powerbi_ready_date.csv"
    workbook = tmp_path / "powerbi_ready.xlsx"
    readiness_path = tmp_path / "powerbi_ready_readiness.json"
    change_log = tmp_path / "pipeline_report.json"
    rejected_path = tmp_path / "sales_rejected.csv"
    assert sales_path.is_file()
    assert date_path.is_file()
    assert workbook.stat().st_size > 0
    assert readiness_path.is_file()
    assert change_log.is_file()
    assert rejected_path.is_file()

    sales_text = sales_path.read_text(encoding="utf-8")
    assert "001" in sales_text
    assert "₹" not in sales_text

    sales = pd.read_csv(sales_path, dtype={"order_id": "string", "customer_id": "string"})
    assert sales["order_id"].tolist() == [
        "1001",
        "1002",
        "1003",
        "1006",
        "1007",
        "1008",
        "1009",
        "1010",
    ]
    assert sales.loc[sales["order_id"] == "1001", "customer_id"].item() == "001"
    assert sales.loc[sales["order_id"] == "1001", "city"].item() == "Hyderabad"
    assert sales.loc[sales["order_id"] == "1002", "city"].item() == "Bengaluru"
    assert sales.loc[sales["order_id"] == "1003", "city"].item() == "Hyderabad"
    assert sales.loc[sales["order_id"] == "1006", "city"].item() == "Mumbai"
    assert sales.loc[sales["order_id"] == "1009", "city"].item() == "New Delhi"
    assert sales.loc[sales["order_id"] == "1001", "amount"].item() == 1250.5
    assert sales.loc[sales["order_id"] == "1009", "amount"].item() == 12000
    assert sales.loc[sales["order_id"].isin(["1007", "1008"]), "amount"].isna().all()
    assert pd.to_datetime(sales["order_date"]).min() == pd.Timestamp("2025-01-15")
    assert pd.to_datetime(sales["order_date"]).max() == pd.Timestamp("2025-02-03")

    rejected = pd.read_csv(rejected_path)
    assert rejected["Order ID"].astype(str).tolist() == ["1004", "1005"]

    dates = pd.to_datetime(pd.read_csv(date_path)["date"])
    assert len(dates) == 20
    assert dates.min() == pd.Timestamp("2025-01-15")
    assert dates.max() == pd.Timestamp("2025-02-03")
    assert dates.is_monotonic_increasing
    assert (dates.diff().dropna() == pd.Timedelta(days=1)).all()
    date_table = pd.read_csv(date_path)
    first = date_table.iloc[0]
    assert int(first["fiscal_year"]) == 2025
    assert int(first["fiscal_month"]) == 10

    readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
    assert readiness["is_ready"] is True
    assert readiness["tables"]["sales"]["field_types"] == {
        "order_id": "Text",
        "customer_id": "Text",
        "city": "Text",
        "order_date": "Date",
        "amount": "Decimal Number",
        "channel": "Text",
    }
    relationship = readiness["relationships"][0]
    assert relationship["from_table"] == "sales"
    assert relationship["from_columns"] == ["order_date"]
    assert relationship["to_table"] == "date"
    assert relationship["to_columns"] == ["date"]
    assert relationship["cardinality"] == "many_to_one"

    report = json.loads(change_log.read_text(encoding="utf-8"))
    assert report["is_ready"] is True
    changes = {item["step"]: item for item in report["changes"]}
    assert changes["column:order_date"]["removed_rows"] == 2
    assert changes["finish/DuplicateRemover"]["removed_rows"] == 1
    assert "Readiness score: 100.0" in completed.stdout


def test_quickstart_notebook_records_a_short_recipe_run() -> None:
    notebook_path = Path(__file__).resolve().parents[1] / "notebooks" / "quickstart.ipynb"
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    sources = []
    for cell in notebook["cells"]:
        source = cell["source"]
        sources.append("".join(source) if isinstance(source, list) else source)
    combined = "\n".join(sources)
    for snippet in (
        '"pip", "install"',
        "edf.profile",
        ".preview(",
        ".apply(",
        "recipe.save",
        "PipelineRecipe.load",
    ):
        assert snippet in combined
    assert any(cell.get("outputs") for cell in notebook["cells"] if cell["cell_type"] == "code")
