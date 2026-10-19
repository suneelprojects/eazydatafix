"""Run a synthetic sales-file demonstration from the repository root."""

from pathlib import Path

import eazydatafix as edf


def main() -> None:
    """Preview, apply and repeat a versioned preparation recipe."""
    root = Path(__file__).resolve().parent
    recipe = edf.PipelineRecipe.load(root / "v2_sales_recipe.json")
    pipeline = edf.Pipeline(recipe)
    plan = pipeline.preview(root / "v2_sales.csv")
    print("Reviewed stages:", plan.selected_steps)
    print(plan.result.dataset.to_string(index=False))
    result = pipeline.apply(root / "v2_sales.csv", plan)
    print("Readiness:", result.status)
    print("Recorded transformations:", len(result.changes))
    if not result.is_ready:
        raise RuntimeError(result.report())


if __name__ == "__main__":
    main()
