# EazyDataFix 2.0 Migration Guide

Upgrade with `pip install --upgrade eazydatafix==2.0.0`.
Existing v1 Python convenience APIs keep their defaults and return types; working
notebooks do not need to migrate. The new recipe API is opt-in.

## Adopt reusable preparation

1. Define `PipelineRecipe(columns={...})` using explicit `ColumnRule` values.
2. Save the recipe as JSON, or install the `yaml` extra for YAML.
3. Call `Pipeline(recipe).preview(source)` and inspect `plan.result.report()`.
4. Call `pipeline.apply(source, plan)` and export only when `result.is_ready`.
5. Reload the same recipe for later files, or use the `edf --recipe` CLI.

Recipe defaults deliberately differ from legacy automatic cleaning: type inference
is disabled, missing values and empty structures are kept, and exact duplicates
are removed after explicit conversion. `on_error="reject"` is the default for
invalid declared conversions. `number` uses floating-point storage. Datetime rules
require an explicit format. Column-rule names use normalized headings.

Recipes support all three readiness workflows. Use the recipe-bound ML artifact
to prepare raw prediction data before applying saved training-only parameters.
Preview/apply plans stay within a Python process; JSON/YAML recipes are portable.
A CLI preview and a later CLI run are independent executions.

The CLI now honors supplied cleaning and preparation configs. Check configured
jobs that previously relied on those settings being ignored. New readiness CLI
workflows return nonzero when the readiness gate fails.

See [docs/pipeline_recipes.md](docs/pipeline_recipes.md) for complete examples,
error policies, exports and current scope. Browser Studio is a separate product
integration and does not change when the Python package is upgraded.

---

# EazyDataFix 1.0 Migration Guide

All public APIs available in v0.5.0 remain available in v1.0.0, including
profiling, assessment, cleaning, preparation, deterministic and Agentic EDA,
reports, approval checkpoints, notebook export, and grounded narratives.

## New stable workflows

- `edf.run(...)` composes profile, assessment, cleaning, and EDA.
- `edf.fix(..., FixConfig(dry_run=True))` previews auditable cleaning.
- `edf.prepare_with_report(...)` returns preparation diagnostics.
- `edf.infer_schema(...)` and `edf.validate_contract(...)` support pipeline
  contracts and explicit pass/fail results.
- The `edf` CLI supports JSON/YAML-configured batch processing.

Catch `EazyDataFixError` for stable package-level failures. The historical
`EasyDataFixError` spelling remains available for compatibility. No migration
is required for existing v0.5.0 calls.
