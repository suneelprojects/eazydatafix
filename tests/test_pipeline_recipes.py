"""Regression coverage for reusable v2 preparation, review and readiness workflows."""

import json
from dataclasses import replace

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

import eazydatafix as edf
from eazydatafix.cli import main
from eazydatafix.pipeline.audit import dataset_fingerprint
from eazydatafix.pipeline.conversion import ExplicitConverter


@pytest.fixture
def sales() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Customer ID": ["001", "002", "003"],
            "Amount": ["₹1,250.50", "₹800", "₹2,300"],
            "Order Date": ["01/02/2025", "02/02/2025", "03/02/2025"],
            "City": [" HYD ", "BLR", "Hyderabad"],
        }
    )


@pytest.fixture
def recipe() -> edf.PipelineRecipe:
    return edf.PipelineRecipe(
        name="monthly_sales",
        columns={
            "customer_id": edf.ColumnRule(dtype="string"),
            "amount": edf.ColumnRule(dtype="number", currency_symbols=("₹",)),
            "order_date": edf.ColumnRule(dtype="datetime", date_format="%d/%m/%Y"),
            "city": edf.ColumnRule(
                dtype="string", category_mapping={"HYD": "Hyderabad", "BLR": "Bengaluru"}
            ),
        },
    )


@pytest.mark.parametrize("suffix", [".json", ".yaml", ".yml"])
def test_recipe_roundtrip(tmp_path, recipe, suffix):
    if suffix != ".json":
        pytest.importorskip("yaml")
    path = tmp_path / f"recipe{suffix}"
    recipe.save(path)
    restored = edf.PipelineRecipe.load(path)
    assert restored.to_dict() == recipe.to_dict()
    restored.columns.clear()
    assert recipe.columns


@pytest.mark.parametrize(
    "payload",
    [
        {"unknown": True},
        {"recipe_format_version": 2},
        {"recipe_format_version": True},
        {"detailed_audit": "false"},
        {"columns": {"value": {"dtype": "string", "typo": 1}}},
        {"fix_config": {"remove_duplicates": "false"}},
        {"audit_sample_size": 101},
        {"columns": {"value": {"date_format": 1}}},
        {"quality_rules": [{"name": "x"}]},
    ],
)
def test_recipe_rejects_invalid_config(payload):
    with pytest.raises((ValueError, TypeError)):
        edf.PipelineRecipe.from_dict(payload)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"dtype": "datetime"},
        {"dtype": "float"},
        {"on_error": "coerce"},
        {"decimal_separator": ",", "thousands_separator": ","},
        {"category_mapping": {"a": "b", "b": "c"}},
        {"fill_value": float("nan")},
    ],
)
def test_column_rule_rejects_ambiguous_or_invalid_rules(kwargs):
    with pytest.raises((TypeError, ValueError)):
        edf.ColumnRule(**kwargs)


def test_preview_apply_and_idempotency_preserve_source(sales, recipe):
    original = sales.copy(deep=True)
    pipeline = edf.Pipeline(recipe)
    plan = pipeline.preview(sales)
    assert plan.result.dry_run
    assert plan.result.is_ready
    applied = pipeline.apply(sales, plan)
    assert not applied.dry_run
    assert_frame_equal(original, sales)
    assert_frame_equal(plan.result.dataset, applied.dataset)
    assert applied.dataset.customer_id.tolist() == ["001", "002", "003"]
    assert applied.dataset.amount.tolist() == [1250.5, 800.0, 2300.0]
    assert applied.dataset.order_date.iloc[0] == pd.Timestamp("2025-02-01")
    assert applied.dataset.city.tolist() == ["Hyderabad", "Bengaluru", "Hyderabad"]
    assert_frame_equal(applied.dataset, pipeline.run(applied.dataset).dataset)
    with pytest.raises(edf.WorkflowError, match="Preview"):
        plan.result.save("unused")


def test_csv_tokens_preserved_before_inference(tmp_path):
    source = tmp_path / "ids.csv"
    source.write_text("Customer ID,Value\n00001,10\n00002,20\n", encoding="utf-8")
    pipeline = edf.Pipeline(
        edf.PipelineRecipe(
            columns={
                "customer_id": edf.ColumnRule(dtype="string"),
                "value": edf.ColumnRule(dtype="integer"),
            }
        )
    )
    result = pipeline.run(source)
    assert result.dataset.customer_id.tolist() == ["00001", "00002"]
    assert str(result.dataset.value.dtype) == "Int64"


def test_excel_tokens_and_recipe_export(tmp_path, recipe, sales):
    path = tmp_path / "sales.xlsx"
    sales.to_excel(path, index=False)
    result = edf.Pipeline(recipe).run(path)
    exports = result.save(tmp_path / "exports", formats=("csv", "excel"))
    assert exports["report"].is_file()
    report = json.loads(exports["report"].read_text())
    assert report["is_ready"]
    assert (tmp_path / "exports" / "recipe.json").is_file()


@pytest.mark.parametrize("policy", ["preserve", "reject", "quarantine"])
def test_conversion_failures_have_evidence_and_explicit_policies(policy):
    data = pd.DataFrame(
        {"amount": ["10", "unknown", "30"], "name": ["a", "b", "c"]}, index=[7, 7, 2]
    )
    original = data.copy()
    recipe = edf.PipelineRecipe(columns={"amount": edf.ColumnRule(dtype="number", on_error=policy)})
    result = edf.Pipeline(recipe).run(data)
    issue = next(item for item in result.issues if item.code == "conversion_failed")
    assert issue.count == 1
    assert issue.samples[0]["row_position"] == 1
    assert issue.samples[0]["value"] == "unknown"
    assert_frame_equal(data, original)
    if policy == "quarantine":
        assert result.dataset.amount.tolist() == [10, 30]
        assert result.rejected_rows["data"].amount.tolist() == ["unknown"]
        assert any(change.removed_rows == 1 for change in result.changes)
    else:
        assert result.dataset.amount.tolist() == ["10", "unknown", "30"]
        assert result.rejected_rows["data"].empty
    if policy == "reject":
        assert result.status == "failed"
        with pytest.raises(edf.WorkflowError, match="not ready"):
            result.save("unused")


def test_quarantine_export_contains_original_rejected_values(tmp_path):
    data = pd.DataFrame({"amount": ["10", "bad", "30"], "city": ["a", "b", "c"]})
    recipe = edf.PipelineRecipe(
        columns={"amount": edf.ColumnRule(dtype="number", on_error="quarantine")}
    )
    result = edf.Pipeline(recipe).run(data)
    assert result.is_ready
    result.save(tmp_path / "output")
    rejected = pd.read_csv(tmp_path / "output" / "data_rejected.csv")
    assert rejected.amount.tolist() == ["bad"]


def test_quarantining_all_rows_is_an_explained_failure():
    recipe = edf.PipelineRecipe(
        columns={"amount": edf.ColumnRule(dtype="number", on_error="quarantine")}
    )
    result = edf.Pipeline(recipe).run(pd.DataFrame({"amount": ["bad", "worse"]}))
    assert not result.is_ready
    assert any(issue.code == "empty_dataset" for issue in result.issues)
    assert len(result.rejected_rows["data"]) == 2


@pytest.mark.parametrize(
    "values,rule,expected",
    [
        (
            ["9007199254740993", "9223372036854775807"],
            edf.ColumnRule(dtype="integer"),
            [9007199254740993, 9223372036854775807],
        ),
        (
            ["1.234,50", "2.100,25"],
            edf.ColumnRule(dtype="number", decimal_separator=",", thousands_separator="."),
            [1234.5, 2100.25],
        ),
        (["25%", "0.5"], edf.ColumnRule(dtype="number", percentage=True), [0.25, 0.5]),
        (["yes", "NO"], edf.ColumnRule(dtype="boolean"), [True, False]),
    ],
)
def test_explicit_conversion_is_exact_and_idempotent(values, rule, expected):
    result = ExplicitConverter.convert(pd.Series(values), rule)
    assert not result.invalid.any()
    assert result.values.tolist() == expected
    again = ExplicitConverter.convert(result.values, rule)
    assert result.values.equals(again.values)


@pytest.mark.parametrize("value", ["1.5", "9223372036854775808", "-9223372036854775809", "inf"])
def test_integer_conversion_does_not_round_or_overflow(value):
    converted = ExplicitConverter.convert(pd.Series([value]), edf.ColumnRule(dtype="integer"))
    assert converted.invalid.tolist() == [True]


def test_literal_mapping_and_constant_fill():
    rule = edf.ColumnRule(
        dtype="string",
        missing_markers=("unknown",),
        fill_value="Hyderabad",
        category_mapping={"HYD": "Hyderabad"},
    )
    result = ExplicitConverter.convert(pd.Series(["HYD", "unknown", None]), rule)
    assert result.values.tolist() == ["Hyderabad"] * 3


def test_declared_string_survives_heuristic_preparation():
    recipe = edf.PipelineRecipe(
        columns={"code": edf.ColumnRule(dtype="string")},
        fix_config=edf.FixConfig(missing_value_strategy="keep"),
        prepare_config=edf.PrepareConfig(),
    )
    result = edf.Pipeline(recipe).run(
        pd.DataFrame({"code": ["001", "002"], "amount": ["10", "20"]})
    )
    assert result.dataset.code.tolist() == ["001", "002"]
    assert str(result.dataset.code.dtype) == "string"


def test_selective_review_and_dependency_validation(sales, recipe):
    pipeline = edf.Pipeline(recipe)
    selected = ["data/clean", "data/column:amount", "readiness"]
    preview = pipeline.preview(sales, selected_steps=selected)
    result = pipeline.apply(sales, preview)
    assert result.dataset.amount.tolist() == [1250.5, 800, 2300]
    assert result.dataset.city.tolist() == ["HYD", "BLR", "Hyderabad"]
    assert "data/column:city" in result.skipped_steps
    for bad in (
        ["data/column:amount", "readiness"],
        ["data/clean"],
        ["bad", "readiness"],
        ["readiness", "readiness"],
        "readiness",
    ):
        with pytest.raises(ValueError):
            pipeline.preview(sales, selected_steps=bad)


def test_review_rejects_changed_source_recipe_and_preview(sales, recipe):
    pipeline = edf.Pipeline(recipe)
    plan = pipeline.preview(sales)
    changed = sales.copy()
    changed.iloc[0, 1] = "₹9,000"
    with pytest.raises(edf.WorkflowError, match="Source"):
        pipeline.apply(changed, plan)
    with pytest.raises(edf.WorkflowError, match="Recipe"):
        edf.Pipeline(replace(recipe, name="different")).apply(sales, plan)
    plan.result.dataset.iloc[0, 1] = 999
    with pytest.raises(edf.WorkflowError, match="modified"):
        pipeline.apply(sales, plan)


def test_pipeline_snapshots_mutable_caller_recipe(sales, recipe):
    pipeline = edf.Pipeline(recipe)
    plan = pipeline.preview(sales)
    recipe.columns.clear()
    recipe.fix_config.convert_data_types = True
    assert_frame_equal(pipeline.apply(sales, plan).dataset, plan.result.dataset)


def test_contract_failures_gate_exports(tmp_path):
    recipe = edf.PipelineRecipe(
        columns={"amount": edf.ColumnRule(dtype="integer")},
        contract=edf.DataContract((edf.SchemaField("amount", "Int64", False),)),
        quality_rules=(edf.QualityRule("positive_amount", "amount", "min", 0),),
    )
    result = edf.Pipeline(recipe).run(pd.DataFrame({"amount": ["10", "-5"]}))
    assert not result.is_ready
    assert result.validations["data"]["passed"] is False
    with pytest.raises(edf.WorkflowError):
        result.save(tmp_path / "invalid")
    assert not (tmp_path / "invalid").exists()


def test_missing_required_column_fails_with_explanation():
    recipe = edf.PipelineRecipe(columns={"absent": edf.ColumnRule(dtype="string")})
    result = edf.Pipeline(recipe).run(pd.DataFrame({"value": [1, 2]}))
    assert any(item.code == "missing_column" for item in result.issues)
    assert not result.is_ready


def test_bounded_and_detailed_audit_have_original_row_positions():
    recipe = edf.PipelineRecipe(
        audit_sample_size=1,
        detailed_audit=True,
        columns={"amount": edf.ColumnRule(dtype="integer")},
    )
    result = edf.Pipeline(recipe).run(pd.DataFrame({"amount": ["10", "20", "30"]}))
    conversion = next(change for change in result.changes if change.step == "column:amount")
    assert conversion.changed_values == 3
    assert len(conversion.samples) == 1
    assert len(conversion.details) == 3
    assert conversion.details[-1]["row_position"] == 2
    assert conversion.dtype_changes["amount"] == (str(pd.Series(["10", "20", "30"]).dtype), "Int64")
    json.dumps(result.report(), allow_nan=False)


def test_fingerprint_binds_order_and_types():
    data = pd.DataFrame({"value": [1, 2]})
    original = dataset_fingerprint({"data": data})
    assert original != dataset_fingerprint({"data": data.iloc[::-1]})
    assert original != dataset_fingerprint({"data": data.astype("string")})


def test_ml_recipe_artifact_prepares_raw_prediction_data(tmp_path):
    data = pd.DataFrame(
        {
            "amount": ["₹10", "₹30", "₹20", "₹50", "₹80", "₹60"],
            "city": ["HYD", "BLR", "HYD", "BLR", "HYD", "BLR"],
            "churn": ["0", "1", "1", "0", "1", "0"],
        }
    )
    recipe = edf.PipelineRecipe(
        workflow="ml_ready",
        target="churn",
        columns={
            "amount": edf.ColumnRule(dtype="number", currency_symbols=("₹",)),
            "city": edf.ColumnRule(dtype="string", category_mapping={"HYD": "Hyderabad"}),
            "churn": edf.ColumnRule(dtype="integer"),
        },
        ml_config=edf.MLReadyConfig(
            shuffle=False, test_size=0.33, drop_high_cardinality=False, scaling="standard"
        ),
    )
    result = edf.Pipeline(recipe).run(data)
    assert result.is_ready
    assert result.readiness_result.artifact.scale_parameters["amount"]["mean"] == 27.5
    raw_features = data.iloc[:2].drop(columns="churn")
    transformed = result.artifact.transform(raw_features)
    assert len(transformed) == 2
    path = tmp_path / "artifact.json"
    result.artifact.to_json(path)
    restored = edf.RecipeMLArtifact.from_json(path)
    assert_frame_equal(transformed, restored.transform(raw_features))
    result.save(tmp_path / "exports")
    assert (tmp_path / "exports" / "ml_ready_recipe_artifact.json").is_file()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"columns": {"value": edf.ColumnRule(dtype="number", fill_value=0)}},
        {"fix_config": edf.FixConfig(missing_value_strategy="mean")},
        {"prepare_config": edf.PrepareConfig(outlier_action="cap", infer_types=False)},
        {"prepare_config": edf.PrepareConfig()},
    ],
)
def test_ml_recipes_block_full_dataset_fitting(kwargs):
    with pytest.raises(ValueError):
        edf.PipelineRecipe(workflow="ml_ready", target="label", **kwargs)


def test_powerbi_recipe_validates_multiple_tables_and_date_dimension(tmp_path):
    recipe = edf.PipelineRecipe(
        workflow="powerbi_ready",
        table_columns={
            "sales": {
                "customer_id": edf.ColumnRule(dtype="string"),
                "amount": edf.ColumnRule(dtype="number"),
                "order_date": edf.ColumnRule(dtype="datetime", date_format="%Y-%m-%d"),
            },
            "customers": {"customer_id": edf.ColumnRule(dtype="string")},
        },
        powerbi_config=edf.PowerBIReadyConfig(
            keys=(edf.PowerBIKey("customers", ("customer_id",)),),
            relationships=(
                edf.PowerBIRelationship("sales", ("customer_id",), "customers", ("customer_id",)),
            ),
            generate_date_table=True,
            date_columns={"sales": ("order_date",)},
        ),
    )
    tables = {
        "sales": pd.DataFrame(
            {
                "customer_id": ["001", "002"],
                "amount": ["10", "20"],
                "order_date": ["2025-01-01", "2025-01-03"],
            }
        ),
        "customers": pd.DataFrame({"customer_id": ["001", "002"], "city": ["a", "b"]}),
    }
    result = edf.Pipeline(recipe).run(tables)
    assert result.is_ready
    assert len(result.tables["date"]) == 3
    assert result.tables["sales"].customer_id.tolist() == ["001", "002"]
    result.save(tmp_path / "powerbi", formats=("csv", "excel"))
    assert (tmp_path / "powerbi" / "powerbi_ready.xlsx").is_file()


def test_cli_recipe_preview_and_apply(tmp_path, sales, recipe):
    csv = tmp_path / "sales.csv"
    sales.to_csv(csv, index=False)
    recipe_path = tmp_path / "recipe.json"
    recipe.save(recipe_path)
    output = tmp_path / "summary.json"
    root = tmp_path / "exports"
    args = [
        str(csv),
        "--recipe",
        str(recipe_path),
        "--output",
        str(output),
        "--export-dir",
        str(root),
    ]
    assert main([*args, "--preview"]) == 0
    assert not list(root.rglob("*.csv"))
    assert json.loads(output.read_text())["records"][0]["summary"]["dry_run"]
    assert main(args) == 0
    assert (root / "001_sales" / "data.csv").is_file()


def test_cli_cleaning_config_is_passed_to_engine(tmp_path):
    csv = tmp_path / "values.csv"
    csv.write_text("value\n1\n1\n2\n", encoding="utf-8")
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"workflow": "fix", "fix_config": {"remove_duplicates": False}}))
    output = tmp_path / "summary.json"
    assert main([str(csv), "--config", str(config), "--output", str(output)]) == 0
    assert json.loads(output.read_text())["records"][0]["summary"]["rows"] == 3


def test_cli_invalid_recipe_is_configuration_failure(tmp_path):
    path = tmp_path / "recipe.json"
    path.write_text('{"workflow":"ml_ready"}')
    assert main(["--recipe", str(path), "data.csv"]) == 2
    assert main(["--preview", "data.csv"]) == 2


def test_cli_failed_conversion_returns_nonzero_and_exports_no_clean_data(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text("amount\n10\nbad\n")
    recipe_path = tmp_path / "recipe.json"
    edf.PipelineRecipe(columns={"amount": edf.ColumnRule(dtype="integer")}).save(recipe_path)
    root = tmp_path / "output"
    assert main([str(path), "--recipe", str(recipe_path), "--export-dir", str(root)]) == 1
    assert list(root.rglob("pipeline_report.json"))
    assert not list(root.rglob("*.csv"))


def test_changed_applied_data_cannot_be_exported(sales, recipe, tmp_path):
    result = edf.Pipeline(recipe).run(sales)
    result.dataset.iloc[0, 1] = 999
    with pytest.raises(edf.WorkflowError, match="changed"):
        result.save(tmp_path / "output")
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("headings", [["A B", "A-B"], ["!!!", "value"]])
def test_colliding_or_empty_normalized_headings_are_rejected(headings):
    with pytest.raises(ValueError, match="headings"):
        edf.Pipeline(edf.PipelineRecipe()).run(pd.DataFrame([[1, 2]], columns=headings))


def test_duplicate_csv_headings_are_rejected_before_pandas_mangling(tmp_path):
    path = tmp_path / "duplicate.csv"
    path.write_text("amount,amount\n1,2\n")
    with pytest.raises(ValueError, match="unique column headings"):
        edf.Pipeline(edf.PipelineRecipe()).run(path)


def test_bad_missing_strategy_is_rejected_when_recipe_is_loaded():
    with pytest.raises(ValueError, match="Unsupported missing value strategy"):
        edf.PipelineRecipe.from_dict({"fix_config": {"missing_value_strategy": "typo"}})


def test_cli_named_tables_and_gate_failure(tmp_path):
    sales = tmp_path / "sales.csv"
    customers = tmp_path / "customers.csv"
    sales.write_text("customer_id,amount\n001,10\n002,20\n")
    customers.write_text("customer_id,city\n001,a\n002,b\n")
    recipe = edf.PipelineRecipe(
        workflow="powerbi_ready",
        columns={"customer_id": edf.ColumnRule(dtype="string")},
        powerbi_config=edf.PowerBIReadyConfig(
            keys=(edf.PowerBIKey("customers", ("customer_id",)),)
        ),
    )
    path = tmp_path / "recipe.json"
    recipe.save(path)
    args = [
        "--recipe",
        str(path),
        "--table",
        f"sales={sales}",
        "--table",
        f"customers={customers}",
        "--export-dir",
        str(tmp_path / "exports"),
    ]
    assert main(args) == 0
    assert (tmp_path / "exports" / "001_model" / "powerbi_ready_sales.csv").is_file()
    customers.write_text("customer_id,city\n001,a\n001,b\n")
    assert main(args) == 1


@pytest.mark.parametrize("workflow", ["analysis_ready", "ml_ready", "powerbi_ready"])
def test_native_readiness_cli_workflows(tmp_path, workflow):
    data = tmp_path / "data.csv"
    data.write_text("value,label\n10,0\n30,1\n20,1\n50,0\n80,1\n60,0\n")
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"workflow": workflow, "target": "label"}))
    output = tmp_path / "summary.json"
    assert main([str(data), "--config", str(config), "--output", str(output)]) == 0
    assert json.loads(output.read_text())["records"][0]["summary"]["is_ready"]


def test_recipe_inference_never_silently_quarantines_prediction_rows():
    recipe = edf.PipelineRecipe(
        workflow="ml_ready",
        target="label",
        columns={
            "amount": edf.ColumnRule(dtype="number", on_error="quarantine"),
            "label": edf.ColumnRule(dtype="integer"),
        },
        ml_config=edf.MLReadyConfig(shuffle=False, test_size=0.33),
    )
    result = edf.Pipeline(recipe).run(
        pd.DataFrame({"amount": ["10", "30", "20", "50", "80", "60"], "label": [0, 1, 1, 0, 1, 0]})
    )
    assert result.artifact is not None
    with pytest.raises(edf.WorkflowError, match="quarantine"):
        result.artifact.transform(pd.DataFrame({"amount": ["10", "bad"]}))


def test_duplicate_excel_headings_are_rejected_before_pandas_mangling(tmp_path):
    path = tmp_path / "duplicate.xlsx"
    pd.DataFrame([[1, 2]], columns=["amount", "amount"]).to_excel(path, index=False)
    with pytest.raises(ValueError, match="unique column headings"):
        edf.Pipeline(edf.PipelineRecipe()).run(path)
