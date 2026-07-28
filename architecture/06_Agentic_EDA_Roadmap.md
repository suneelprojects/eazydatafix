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

## Next Milestone: Tool-Driven Analysis Execution

The next phase will execute selected plan steps through deterministic tools and
record their outputs for reproducible downstream analysis.

## Future Milestone: LLM Narratives

LLM-generated explanations will be optional and will use the deterministic EDA
result as their source of truth. Generated text will not replace calculated
metrics.
