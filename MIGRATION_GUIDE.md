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
