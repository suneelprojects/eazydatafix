# Reusable preparation recipes (v2.0.0)

Install with `pip install --upgrade eazydatafix==2.0.0`.
YAML recipes require `pip install 'eazydatafix[yaml]==2.0.0'`.
For development, install a local checkout with `pip install -e '.[dev,yaml]'`.

## Prepare a sales file

```python
import eazydatafix as edf

recipe = edf.PipelineRecipe(
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
recipe.save("monthly_sales.json")
pipeline = edf.Pipeline(edf.PipelineRecipe.load("monthly_sales.json"))
plan = pipeline.preview("sales.csv")
print(plan.selected_steps)
print(plan.result.dataset)
print(plan.result.report())
result = pipeline.apply("sales.csv", plan)
if result.is_ready:
    result.save("sales_output", formats=("csv", "excel"))
```

Column-rule names refer to the headings **after** the configured normalization:
`Customer ID` becomes `customer_id`. Duplicate or colliding headings are rejected
with an explanatory error. CSV/Excel loading preserves tokens before conversion;
leading zeroes that an upstream program already discarded cannot be recovered.

## Processing and review order

The same existing engines power both previews and applied results. Stages run in
this order for each table:

1. `data/clean`: configured heading normalization, whitespace trimming, missing
   markers, and optional automatic conversion. Explicit rule columns are protected
   from automatic conversion.
2. `data/column:<name>`: one declared column rule, in sorted column-name order.
3. `data/finish`: configured duplicate/empty-row/empty-column removal and missing
   value strategies. These run after explicit conversions and category mappings.
4. `data/prepare`: preparation controls such as text normalization, outlier handling
   and date-part derivation. Declared types are protected from heuristic conversion.
5. `readiness`: contract checks and the chosen native readiness workflow.

Recipes default to keeping missing values, disabling inferred conversions and
retaining empty structures. Exact duplicate removal is enabled, and is visible
in the `finish` stage. Existing v1 convenience functions retain their own defaults.

Preview selected stages before applying them:

```python
plan = pipeline.preview(
    "sales.csv",
    selected_steps=["data/clean", "data/column:amount", "readiness"],
)
result = pipeline.apply("sales.csv", plan)
```

Column rules require the table's `clean` stage. `readiness` cannot be skipped.
Changing the source, recipe, selected operations or preview evidence requires a
new preview. `apply()` re-executes and compares the reviewed output. `run()` applies
the whole recipe directly for deliberately configured batch jobs. Neither method
mutates the caller's DataFrame or overwrites a source file.

Review plans are **in-memory Python objects**, not portable authorization tokens.
Recipes are portable JSON/YAML. CLI preview and a later CLI run are independent
runs; a later CLI command does not reuse an earlier approval plan.

## Explicit conversion rules

| `dtype` | Output | Rules |
|---|---|---|
| `string` | pandas string | Preserves leading zeroes in available source tokens |
| `integer` | nullable `Int64` | Exact integer parsing; rejects fractional values and overflow |
| `number` | nullable `Float64` | Declared decimal/thousands separators and currency symbols |
| `boolean` | nullable boolean | true/false, yes/no, y/n, and 1/0 tokens |
| `datetime` | pandas datetime | Requires an explicit `date_format`, including `ISO8601` |
| `category` | pandas categorical | Literal string categories, optionally mapped |
| omitted | source type | Applies declared markers/mappings/fill without imposing a type |

`number` uses floating-point values, not exact financial Decimal storage.
`percentage=True` converts suffixed values such as `25%` to `0.25`; unsuffixed
numeric values are already treated as fractions. Currency symbols are literal
boundary tokens. Separator removal follows the declared convention; it does not
infer a locale or validate regional grouping patterns.

```python
european_amount = edf.ColumnRule(
    dtype="number", decimal_separator=",", thousands_separator=".",
    currency_symbols=("€",),
)
```

Category mappings must not contain chains or cycles. Constant fill values are
literal scalars and are available for analysis/BI recipes. ML recipes keep missing
values until training-only imputation.

## Conversion failure policies

| `on_error` | Behaviour |
|---|---|
| `reject` (default) | Preserve the column and fail the readiness/export gate |
| `preserve` | Preserve the entire column, report a warning, and run readiness checks |
| `quarantine` | Exclude invalid rows, retain their original source values separately, and report evidence |

Failures report the column, invalid count, bounded source values and zero-based
row positions. Source positions describe input order, independent of caller index
labels. A preserved column might still fail a contract or native readiness check.
No usable rows remaining is an explained failure. Quarantine only concerns
conversion failures; arbitrary contract violations fail the gate without dropping rows.

## Evidence and exports

Every pipeline result exposes `status`, `is_ready`, `issues`, `changes`, `tables`,
`rejected_rows`, `before_scores`, `after_scores`, `validations` and `report()`.
`readiness_result` retains the existing profile-specific result object. Scores are
evidence from the existing assessment engine; they do not guarantee business truth.

Audit records include row/column counts, dtype changes, changed-value counts,
removed/added row counts and bounded examples. `audit_sample_size=0` omits examples.
`detailed_audit=True` captures all changed cells and removed/added records and can
use substantial memory. Detailed records and samples can contain source values;
review reports before sharing them.

Only ready, applied, unchanged results can be exported. Changing the output or
evidence after application requires another run/review. Exports include the saved
recipe and `pipeline_report.json`; quarantined source rows get separate CSV files.
Analysis/BI exports support CSV, Excel and optional Parquet. ML split exports are
currently CSV. Failed or preview results remain inspectable through `report()`.

## ML Ready recipes and inference

```python
recipe = edf.PipelineRecipe(
    workflow="ml_ready",
    target="churn",
    columns={
        "amount": edf.ColumnRule(dtype="number", currency_symbols=("₹",)),
        "city": edf.ColumnRule(dtype="string"),
        "churn": edf.ColumnRule(dtype="integer"),
    },
    ml_config=edf.MLReadyConfig(scaling="standard"),
)
result = edf.Pipeline(recipe).run("customers.csv")
if result.is_ready:
    result.save("ml_output")
    artifact = edf.RecipeMLArtifact.from_json("ml_output/ml_ready_recipe_artifact.json")
    X_new = artifact.transform("new_customers_without_target.csv")
```

ML recipes require explicit types and reject pre-split inferred conversion,
imputation and fitted outlier handling. The existing ML engine fits learned
parameters on training rows only. The recipe-bound artifact prepares raw feature
inputs before applying those saved parameters; prediction inputs need not contain
the target. It preserves prediction row count and rejects quarantining prediction
rows. Schema/type problems fail with actionable errors rather than silently using
new fitted parameters. No models are trained or evaluated.

Top-level recipe `fix_config` and `prepare_config` own preparation. Nested
`analysis_ready_config` in native ML/BI configs is replaced with a non-transforming
assessment config to avoid applying a second cleaning pass.

## Multi-table Power BI recipes

```python
recipe = edf.PipelineRecipe(
    workflow="powerbi_ready",
    table_columns={
        "sales": {"customer_id": edf.ColumnRule(dtype="string")},
        "customers": {"customer_id": edf.ColumnRule(dtype="string")},
    },
    powerbi_config=edf.PowerBIReadyConfig(
        keys=(edf.PowerBIKey("customers", ("customer_id",)),),
        relationships=(edf.PowerBIRelationship(
            "sales", ("customer_id",), "customers", ("customer_id",), "many_to_one"
        ),),
    ),
)
result = edf.Pipeline(recipe).run({"sales": "sales.csv", "customers": "customers.csv"})
if result.is_ready:
    result.save("bi_output", formats=("csv", "excel"))
```

`columns` applies to every input table; `table_columns` overrides specific table
rules. Table-rule keys use normalized table names. Table order is sorted for
deterministic output; the first table is the primary convenience dataset.
Existing key, cardinality, orphan-key, field-type and date-dimension diagnostics
remain available in `readiness_result`. This prepares model inputs, not `.pbix` files.

## Command line

```bash
edf sales.csv --recipe monthly_sales.json --preview --output preview.json
edf sales.csv --recipe monthly_sales.json --export-dir output
edf sales.csv --recipe monthly_sales.json --preview \
  --select-step data/clean --select-step data/column:amount --select-step readiness
edf --recipe bi_recipe.json --table sales=sales.csv --table customers=customers.csv \
  --export-dir output --format csv --format excel
```

Recipe previews can write report JSON but never clean-data exports. Invalid recipe
configuration exits with `2`; processing or readiness failures exit with `1`;
successful runs exit with `0`. Batch export directories have a stable numeric prefix
to avoid collisions between files sharing a basename. `--recipe` and `--config`
cannot be combined. For legacy configurations, `fix_config`, `prepare_config` and
the three readiness workflows now reach their corresponding engines. ML native
configuration requires `target`.

## Compatibility and scope

V1 convenience functions and return types remain compatible. New `protected_columns`
controls default to empty; `PrepareConfig.infer_types` defaults to `True`, preserving
legacy behaviour. The new recipe API intentionally has conservative defaults.

The pipeline uses pandas in memory. Streaming, SQL connectors, backend/Studio
integration and portable approval plans are future work. A PyPI upgrade updates
the Python package; the browser Studio requires a separate integration.
