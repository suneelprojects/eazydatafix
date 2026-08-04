"""Configuration for optional grounded Agentic EDA narratives."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AgenticEDANarrativeConfig:
    """Limits the deterministic evidence supplied to a narrative provider."""

    max_findings: int = 5
    max_next_steps: int = 5
    max_unresolved_questions: int = 5
    include_workflow_warnings: bool = True

    def __post_init__(self) -> None:
        """Validate narrative evidence limits and feature settings."""
        for name, value in (
            ("max_findings", self.max_findings),
            ("max_next_steps", self.max_next_steps),
            ("max_unresolved_questions", self.max_unresolved_questions),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an int.")

            if value < 0:
                raise ValueError(f"{name} must be at least 0.")

        if not isinstance(self.include_workflow_warnings, bool):
            raise TypeError("include_workflow_warnings must be a bool.")
