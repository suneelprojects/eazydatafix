# Agentic EDA Roadmap

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

## Next Milestone: Grounded Presentation and Export

The next phase will render deterministic workflow outputs into notebooks and
visualisation artifacts, with explicit human checkpoints for domain-dependent
decisions.

## Future Milestone: LLM Narratives

LLM-generated explanations will be optional and will use the deterministic EDA
result as their source of truth. Generated text will not replace calculated
metrics.
