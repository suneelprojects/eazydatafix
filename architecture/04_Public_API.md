# EazyDataFix Public API

## Design Philosophy

The public API is intentionally small, discoverable, deterministic, and
backward compatible. Users begin with:

```python
import eazydatafix as edf
```

## Data Quality and Preparation

```python
profile = edf.profile("employees.csv")
assessment = edf.assess("employees.csv")
ai_readiness = edf.assess_ai_readiness("employees.csv")
fixed = edf.fix("employees.csv")
prepared = edf.prepare(fixed.dataset)
analysis_dataset = edf.analysis_ready("employees.csv")
```

`profile`, `assess`, `assess_ai_readiness`, `fix`, `prepare`, and
`analysis_ready` accept pandas DataFrames or supported dataset paths where
applicable.

## Deterministic EDA

Each stage can be used independently:

```python
result = edf.eda("employees.csv")
plan = edf.plan_eda(result)
execution = edf.execute_eda(
    "employees.csv",
    result=result,
    plan=plan,
)
```

Or as one deterministic workflow:

```python
workflow = edf.run_agentic_eda("employees.csv")
```

The workflow does not call an LLM. It retains the EDA result, analysis plan,
execution result, priority findings, follow-up actions, recommended
visualisations, unresolved questions, warnings, summary, and overall status.

## Agentic EDA Reporting

```python
report = edf.export_agentic_eda_report(
    workflow,
    dataset="employees.csv",
    output_dir="eda-report",
    formats=["html", "json", "markdown"],
)
```

HTML and JSON are default formats. Markdown is optional. The dataset argument
is optional and is used only for chart types that honestly require raw
observations.

## Agentic EDA Notebook Export

```python
notebook = edf.export_agentic_eda_notebook(
    workflow,
    dataset="employees.csv",
    output_path="agentic-eda.ipynb",
)
```

The exporter creates an unexecuted notebook-format v4 document with stable
Markdown and code cells for each deterministic workflow stage. File inputs use
a portable relative reference with an original-path fallback. DataFrame inputs
produce a deterministic JSON companion file beside the notebook.

Pass the same `AgenticEDAConfig` used to create a customised workflow when its
settings must be reproduced explicitly in the notebook:

```python
notebook = edf.export_agentic_eda_notebook(
    workflow,
    dataset=dataframe,
    output_path="agentic-eda.ipynb",
    config=config,
)
```

Notebook generation does not require Jupyter or `nbformat`.

## Supported Inputs

- pandas DataFrame
- CSV
- Excel
- JSON
- Parquet with the optional `parquet` extra

All supported sources route through the shared datasource loading system.

## Public Result and Configuration Models

- `AgenticEDAConfig`
- `AgenticEDANotebookResult`
- `AgenticEDAResult`
- `AgenticEDAReportResult`
- `EDAResult`
- `EDAPlan` and `EDAPlanStep`
- `EDAExecutionResult` and `EDAExecutionStepResult`
- `FollowUpAction`
- `PriorityFinding`
- `UnresolvedQuestion`
- `VisualisationRecommendation`
- `GeneratedVisualisation`
- `SkippedVisualisation`
- `FixConfig` and `FixResult`
- `AssessmentReport`
- `AIReadinessReport`
- `DatasetProfile`
- `ReadyResult`

All official root exports are declared in `eazydatafix.__all__`.

## Compatibility

Version 0.3.0 preserves the public APIs available in 0.2.1 and adds the
deterministic Agentic EDA workflow and reporting APIs without renaming existing
functions.
