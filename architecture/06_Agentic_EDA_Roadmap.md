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

## Next Milestone: Tool-Driven Analysis

The next phase will define tools that inspect deterministic EDA results,
request focused follow-up analysis, and create reproducible analysis plans.

## Future Milestone: LLM Narratives

LLM-generated explanations will be optional and will use the deterministic EDA
result as their source of truth. Generated text will not replace calculated
metrics.
