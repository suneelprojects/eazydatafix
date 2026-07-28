from dataclasses import dataclass


@dataclass(slots=True)
class EDAPlanStep:
    """
    Represents one deterministic analysis-planning decision.

    A step appears in either ``EDAPlan.selected_steps`` or
    ``EDAPlan.skipped_steps``. Priorities are ``high``, ``medium``, ``low``,
    or ``not_applicable`` for skipped steps.
    """

    name: str
    reason: str
    priority: str
    required_columns: list[str]
    dependencies: list[str]


@dataclass(slots=True)
class EDAPlan:
    """
    Represents a deterministic follow-up analysis plan for an EDA result.
    """

    selected_steps: list[EDAPlanStep]
    skipped_steps: list[EDAPlanStep]
    warnings: list[str]
    deterministic_summary: str
