import importlib.util
import json

import pandas as pd
import pytest

import eazydatafix as edf


def _config(**overrides: object) -> edf.PowerBIReadyConfig:
    """Return a predictable Power BI configuration for focused tests."""
    values = {
        "analysis_ready_config": edf.AnalysisReadyConfig(
            fix_config=edf.FixConfig(
                remove_duplicates=False,
                remove_empty_rows=False,
                remove_empty_columns=False,
            )
        ),
        **overrides,
    }
    return edf.PowerBIReadyConfig(**values)


def test_powerbi_ready_normalizes_fields_types_and_preserves_input() -> None:
    """Power BI fields are collision-free, typed, and caller data stays untouched."""
    dataset = pd.DataFrame(
        {
            "Order ID": ["001", "002"],
            "Order-ID": [10, 20],
            "Amount": [10.5, 20.0],
            "Active": [True, False],
            "Order Date": pd.to_datetime(["2026-01-01", "2026-01-02"]),
        }
    )
    original = dataset.copy(deep=True)

    result = edf.powerbi_ready(dataset, _config())

    assert list(result.dataset.columns) == [
        "order_id",
        "order_id_2",
        "amount",
        "active",
        "order_date",
    ]
    assert result.field_types["data"] == {
        "order_id": "Text",
        "order_id_2": "Whole Number",
        "amount": "Decimal Number",
        "active": "True/False",
        "order_date": "Date",
    }
    assert result.is_ready is True
    pd.testing.assert_frame_equal(dataset, original)


def test_powerbi_ready_flattens_records_and_serializes_collections() -> None:
    """Object records flatten predictably while repeating collections remain one row."""
    dataset = pd.DataFrame(
        {
            "customer": [
                {"name": "Ana", "location": {"city": "Hyd"}},
                {"name": "Ben", "location": {"city": "Vizag"}},
            ],
            "tags": [["new", "web"], ["returning"]],
            "sales": [100, 200],
        }
    )

    result = edf.powerbi_ready(dataset, _config())

    assert list(result.dataset.columns) == [
        "customer_location_city",
        "customer_name",
        "tags",
        "sales",
    ]
    assert result.dataset["customer_location_city"].tolist() == ["Hyd", "Vizag"]
    assert result.dataset["tags"].tolist() == ['["new","web"]', '["returning"]']
    assert any(issue.code == "nested_serialized" for issue in result.issues)
    assert any("Flattened nested record field 'customer'" in change for change in result.changes)


def test_powerbi_ready_flattens_nullable_record_fields() -> None:
    """Missing record values do not prevent deterministic nested-field expansion."""
    dataset = pd.DataFrame({"profile": [{"city": "Hyd"}, None, pd.NA]})

    result = edf.powerbi_ready(dataset, _config())

    assert list(result.dataset.columns) == ["profile_city"]
    assert result.dataset["profile_city"].iloc[0] == "Hyd"
    assert result.dataset["profile_city"].isna().sum() == 2


def test_powerbi_ready_validates_keys_without_dropping_rows() -> None:
    """Duplicate and null candidate keys fail readiness without silently changing data."""
    dataset = pd.DataFrame(
        {
            "Customer ID": ["C1", "C1", None],
            "name": ["A", "B", "C"],
        }
    )

    result = edf.powerbi_ready(
        dataset,
        _config(keys=(edf.PowerBIKey("data", ("Customer ID",)),)),
    )

    assert len(result.dataset) == 3
    assert {issue.code for issue in result.issues} >= {"duplicate_key", "null_key"}
    assert result.is_ready is False


def test_powerbi_ready_keeps_analysis_diagnostics_non_blocking() -> None:
    """Generic analysis findings remain visible while BI model gates decide readiness."""
    dataset = pd.DataFrame({"shipping_city": ["Hyd", "Vizag", "Hyd"], "sales": [1, 2, 3]})

    result = edf.powerbi_ready(dataset, _config())

    analysis_issues = [issue for issue in result.issues if issue.code.startswith("analysis_")]
    assert analysis_issues
    assert all(issue.severity == "warning" for issue in analysis_issues)
    assert result.is_ready is True


def test_powerbi_ready_validates_relationships_and_orphans() -> None:
    """Relationship types, one-side uniqueness, and unmatched keys are audited."""
    tables = {
        "Sales Orders": pd.DataFrame({"Order ID": [1, 2, 3], "Customer ID": ["C1", "C2", "C9"]}),
        "Customers": pd.DataFrame({"Customer ID": ["C1", "C2"], "Customer Name": ["A", "B"]}),
    }
    relationship = edf.PowerBIRelationship(
        "Sales Orders",
        ("Customer ID",),
        "Customers",
        ("Customer ID",),
        "many_to_one",
    )

    result = edf.powerbi_ready(tables, _config(relationships=(relationship,)))

    assert result.primary_table == "sales_orders"
    assert result.relationships[0].to_table == "customers"
    assert any(issue.code == "orphan_relationship_key" for issue in result.issues)
    assert not any(issue.code == "relationship_cardinality" for issue in result.issues)
    assert result.is_ready is True


def test_powerbi_ready_fails_invalid_relationship_cardinality() -> None:
    """A duplicated dimension key cannot pass a many-to-one relationship contract."""
    tables = {
        "sales": pd.DataFrame({"customer_id": ["C1", "C2"], "amount": [10, 20]}),
        "customers": pd.DataFrame({"customer_id": ["C1", "C1"], "name": ["A", "B"]}),
    }
    relationship = edf.PowerBIRelationship(
        "sales", ("customer_id",), "customers", ("customer_id",), "many_to_one"
    )

    result = edf.powerbi_ready(tables, _config(relationships=(relationship,)))

    assert any(issue.code == "relationship_cardinality" for issue in result.issues)
    assert result.is_ready is False


def test_powerbi_ready_fails_relationship_type_mismatch() -> None:
    """Relationship endpoints must use compatible Power BI field families."""
    tables = {
        "sales": pd.DataFrame({"customer_key": [1, 2], "amount": [10, 20]}),
        "customers": pd.DataFrame({"customer_key": ["C1", "C2"], "name": ["A", "B"]}),
    }
    relationship = edf.PowerBIRelationship(
        "sales", ("customer_key",), "customers", ("customer_key",), "many_to_one"
    )

    result = edf.powerbi_ready(tables, _config(relationships=(relationship,)))

    assert any(issue.code == "relationship_type_mismatch" for issue in result.issues)
    assert result.is_ready is False


def test_powerbi_ready_generates_continuous_canonical_date_table() -> None:
    """The optional date dimension spans every day and provides model-friendly parts."""
    dataset = pd.DataFrame(
        {
            "order_id": [1, 2],
            "ordered_at": pd.to_datetime(["2026-04-01 10:30", "2026-04-03 15:45"]),
            "amount": [100, 200],
        }
    )

    result = edf.powerbi_ready(
        dataset,
        _config(
            generate_date_table=True,
            date_columns={"data": ("ordered_at",)},
            fiscal_year_start_month=4,
        ),
    )

    assert list(result.tables) == ["data", "date"]
    assert result.tables["date"]["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2026-04-01",
        "2026-04-02",
        "2026-04-03",
    ]
    assert result.tables["date"]["fiscal_year"].tolist() == [2027, 2027, 2027]
    assert "ordered_at_date" in result.dataset.columns
    assert result.relationships[-1].from_columns == ("ordered_at_date",)
    assert result.field_types["date"]["date_key"] == "Whole Number"
    assert result.is_ready is True


def test_powerbi_ready_exports_csv_excel_and_json_report(tmp_path) -> None:
    """Validated tables export without producing a Power BI report file."""
    result = edf.powerbi_ready(
        pd.DataFrame({"order_id": [1, 2], "amount": [10, 20]}),
        _config(),
    )

    exports = result.save(tmp_path, formats=("csv", "excel"), prefix="sales_model")

    assert all(path.exists() for paths in exports.values() for path in paths)
    assert pd.read_csv(exports["csv"][0]).columns.tolist() == ["order_id", "amount"]
    assert pd.read_excel(exports["excel"][0]).columns.tolist() == ["order_id", "amount"]
    report = json.loads(exports["report"][0].read_text(encoding="utf-8"))
    assert report["report_format_version"] == 1
    assert report["tables"]["data"]["rows"] == 2
    assert not list(tmp_path.glob("*.pbix"))


def test_powerbi_ready_parquet_export_has_optional_dependency_boundary(tmp_path) -> None:
    """Parquet export either succeeds or explains the existing optional extra."""
    result = edf.powerbi_ready(pd.DataFrame({"value": [1, 2]}), _config())

    if importlib.util.find_spec("pyarrow") is None:
        with pytest.raises(ImportError, match=r"eazydatafix\[parquet\]"):
            result.save(tmp_path, formats=("parquet",))
    else:
        exports = result.save(tmp_path, formats=("parquet",))
        assert exports["parquet"][0].exists()


def test_powerbi_ready_is_deterministic() -> None:
    """Equivalent runs preserve table, report, issue, and relationship ordering."""
    dataset = pd.DataFrame(
        {
            "record": [{"b": 2, "a": 1}, {"a": 3, "b": 4}],
            "date": pd.to_datetime(["2026-01-01", "2026-01-03"]),
        }
    )
    config = _config(generate_date_table=True)

    first = edf.powerbi_ready(dataset, config)
    second = edf.powerbi_ready(dataset, config)

    for name in first.tables:
        pd.testing.assert_frame_equal(first.tables[name], second.tables[name])
    assert first.report() == second.report()


@pytest.mark.parametrize(
    "factory",
    [
        lambda: edf.PowerBIReadyConfig(fiscal_year_start_month=13),
        lambda: edf.PowerBIReadyConfig(minimum_readiness_score=80),
        lambda: edf.PowerBIReadyConfig(
            analysis_ready_config=edf.AnalysisReadyConfig(fix_config=edf.FixConfig(dry_run=True))
        ),
        lambda: edf.PowerBIRelationship("a", ("id",), "b", ("x", "y")),
        lambda: edf.PowerBIRelationship("a", ("id",), "b", ("id",), "invalid"),
    ],
)
def test_powerbi_ready_rejects_invalid_configuration(factory: object) -> None:
    """Power BI model declarations fail early when configuration is ambiguous."""
    with pytest.raises((TypeError, ValueError)):
        factory()  # type: ignore[operator]


def test_powerbi_ready_rejects_unknown_export_format(tmp_path) -> None:
    """The exporter cannot imply unsupported PBIX or dashboard generation."""
    result = edf.powerbi_ready(pd.DataFrame({"value": [1]}), _config())

    with pytest.raises(ValueError, match="Unsupported Power BI export"):
        result.save(tmp_path, formats=("pbix",))
