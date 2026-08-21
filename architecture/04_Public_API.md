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

## Controlled Cleaning Workflow

Use `FixConfig` to make cleaning choices explicit and auditable. Rules refer
to the normalized column name when column-name normalization is enabled.

```python
config = edf.FixConfig(
    dry_run=True,
    numeric_conversion_threshold=0.95,
    date_parsing_threshold=0.80,
    column_rules={
        "salary": edf.ColumnCleaningRule(missing_value_strategy="median"),
        "notes": edf.ColumnCleaningRule(trim_whitespace=False),
    },
)
preview = edf.fix("employees.csv", config)

# The caller's data and preview.dataset are unchanged in dry-run mode.
# preview.proposed_dataset holds the deterministic result.
for change in preview.change_log or []:
    print(change.step, change.rows_before, change.rows_after)
```

When `convert_data_types=True`, the controlled pipeline converts numeric text,
currency values, percentages, unambiguous boolean tokens, and date-named
columns only when the corresponding confidence threshold is met. Identifier,
email, and phone columns are protected from automatic numeric conversion.

Use `edf.run(...)` when the deterministic profile, assessment, cleaning, and
EDA stages should be returned together in a `RunResult`.

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

## Agentic EDA Human Approval

Use the explicit two-phase API when a human must review the deterministic plan
before analysis execution:

```python
checkpoint = edf.prepare_agentic_eda_approval(
    "employees.csv",
    config=edf.AgenticEDAConfig(),
)

# Review checkpoint.eda_result and checkpoint.eda_plan.
approved_checkpoint = edf.approve_agentic_eda_plan(
    checkpoint,
    approved_step_ids=None,
    reviewer="Suneel Kumar Kola",
    notes="Approved for execution",
)

workflow = edf.resume_agentic_eda(
    "employees.csv",
    approved_checkpoint,
)
```

Checkpoint preparation performs dataset understanding and planning only. It
does not execute a plan step. `approved_step_ids=None` approves all originally
selected steps; a supplied sequence may approve only a subset of those steps.
Unknown, duplicate, and planner-skipped IDs are rejected. Planner ordering is
preserved. Every dependency required by an approved step must also be listed
explicitly; incomplete subsets fail approval and no dependency is approved
implicitly.

Use `edf.reject_agentic_eda_plan(...)` to record an explicit rejection. Pending
and rejected checkpoints cannot be resumed. Resume verifies the deterministic
dataset fingerprint and checkpoint snapshot integrity, reuses the checkpoint's
EDA result and approved plan, and returns the existing `AgenticEDAResult` type.
`edf.run_agentic_eda(...)` retains its original one-call behaviour and return
type.

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

## Optional Grounded AI Narrative

Generate a presentation only after the deterministic workflow is complete:

```python
from eazydatafix.narratives import OpenAINarrativeProvider

provider = OpenAINarrativeProvider(model="your-openai-model")
narrative = edf.generate_agentic_eda_narrative(workflow, provider)
```

Providers receive only an immutable compact deterministic evidence brief. Each
generated claim must cite supplied evidence IDs. Citation, numeric,
causal-language, and lexical-support validation rejects common unsupported
outputs. A SHA-256 workflow fingerprint prevents a narrative from being
attached to a different or modified workflow. These checks do not prove
semantic truth, so AI-written text still requires human review. Pass the
resulting object to
`edf.export_agentic_eda_report(..., narrative=narrative)` to include it in HTML,
JSON, and Markdown reports; human-readable formats include the cited evidence
details. Install the OpenAI adapter only when required with `pip install
"eazydatafix[openai]"`.

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
- `AgenticEDAApprovalCheckpoint`
- `AgenticEDANotebookResult`
- `AgenticEDANarrative` and `AgenticEDANarrativeConfig`
- `NarrativeClaim` and `NarrativeEvidence`
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

Version 0.4.0 preserves every public API available in 0.3.0 and adds
deterministic notebook export and human approval checkpoint APIs without
renaming existing functions.
