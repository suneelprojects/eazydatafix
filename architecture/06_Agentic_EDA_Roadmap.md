# Agentic EDA Roadmap

Deterministic notebook export and human approval checkpoints are delivered in
EazyDataFix 0.4.0. The next milestone remains optional grounded presentation.

## Foundation: Deterministic EDA

The first Agentic EDA milestone is deterministic. `eazydatafix.eda(...)` loads
a supported dataset through the existing datasource system and returns
structured metrics, observations, and recommendations without calling an LLM.

The foundation provides:

- Dataset shape, columns, and data types
- Missing-value and duplicate-row summaries
- Numeric descriptive statistics and correlations
- Categorical summaries and unique-value counts
- Semantic roles for measures, categories, identifiers, datetimes, and booleans
- Identifier-aware numeric analysis and cardinality recommendations
- Deterministic observations and recommendations

## Milestone 2: Deterministic Analysis Planner

`eazydatafix.plan_eda(...)` converts an existing deterministic EDA result into
a structured follow-up plan. Every supported analysis is explicitly selected
or skipped with a reason, priority, required columns, and dependencies.

The planner covers missing values, duplicates, numeric distributions, outliers,
skewness, correlations, categorical distributions, class imbalance, datetime
trends, boolean distributions, and identifier exclusion without calling an LLM.

## Milestone 3: Deterministic Analysis Execution

`eazydatafix.execute_eda(...)` executes selected plan steps through modular
deterministic handlers and records structured outputs, execution order,
warnings, skipped steps, and step-level status.

The executor validates supplied EDA results against the dataset, preserves input
DataFrames, isolates safe step failures, and exposes JSON-ready output without
calling an LLM.

## Milestone 4: Deterministic Agentic Orchestration

`eazydatafix.run_agentic_eda(...)` composes dataset understanding, planning,
and deterministic execution before generating follow-up actions, priority
findings, visualisation recommendations, and unresolved domain questions.

Every generated decision retains its source execution step, target columns,
priority, reason, and prerequisites. Validated configuration controls the
existing execution thresholds and stable output feature toggles. Partial step
failures remain visible without preventing safe decisions from successful
independent steps.

## Milestone 5: Deterministic Reporting and Visualisation Artifacts

`eazydatafix.export_agentic_eda_report(...)` renders existing workflow outputs
as standalone HTML, stable JSON, optional Markdown, and deterministic PNG
visualisations. Chart handlers generate only orchestrator recommendations and
use structured execution output wherever possible.

Raw-value charts require an optional dataset that is validated against the
workflow before use. Recommendations that cannot be represented honestly are
recorded as skipped rather than fabricated. Successful artifacts survive
independent renderer or chart failures.

## Milestone 6: Deterministic Notebook Export

`eazydatafix.export_agentic_eda_notebook(...)` creates an unexecuted,
ready-to-run notebook-format v4 artifact with stable cells for dataset loading,
understanding, planning, execution, orchestration, findings, and report export.
DataFrame inputs receive a deterministic JSON companion file, and notebook
generation requires no Jupyter runtime dependency.

## Milestone 7: Human Approval Checkpoints

`eazydatafix.prepare_agentic_eda_approval(...)` performs dataset understanding
and deterministic planning without executing analysis steps. The resulting
`AgenticEDAApprovalCheckpoint` preserves the original EDA result, plan,
configuration, reviewer decision fields, and a SHA-256 dataset fingerprint.

Reviewers can approve all originally selected steps, approve a subset while
preserving planner order, or reject the checkpoint explicitly. Subsets must
list required dependencies explicitly; incomplete dependency sets fail before
execution and dependencies are never added implicitly. Resume accepts only
approved checkpoints, verifies that the dataset fingerprint is unchanged,
validates all checkpoint snapshot and decision fields, and reuses the
checkpoint's understanding and plan before invoking the existing executor and
follow-up decision pipeline.

The original `eazydatafix.run_agentic_eda(...)` one-call workflow remains
unchanged for callers that do not require an approval gate.

## Milestone 8: Grounded Presentation

`eazydatafix.generate_agentic_eda_narrative(...)` builds an optional
business-facing presentation from a completed deterministic workflow without
changing calculated metrics. Providers receive only a compact deterministic
evidence brief, never the raw dataset. Every generated claim must cite supplied
evidence IDs; malformed, uncited, duplicate, or unknown citations fail before a
narrative result is returned. The resulting JSON-ready narrative can be included
in HTML, JSON, and Markdown Agentic EDA reports.

The built-in OpenAI Responses API adapter is optional and installed through
`eazydatafix[openai]`. No API key or AI dependency is required for deterministic
EDA, reports, notebooks, or approval checkpoints.

## Future Milestone: LLM Narratives

LLM-generated explanations will be optional and will use the deterministic EDA
result as their source of truth. Generated text will not replace calculated
metrics.
