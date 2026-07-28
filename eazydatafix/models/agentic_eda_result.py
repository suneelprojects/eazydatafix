from dataclasses import dataclass
from typing import Any

from eazydatafix.models.eda_execution_result import EDAExecutionResult
from eazydatafix.models.eda_plan import EDAPlan
from eazydatafix.models.eda_result import EDAResult
from eazydatafix.models.serialization import to_json_compatible


@dataclass(slots=True)
class FollowUpAction:
    """
    Represents a deterministic action recommended by an executed analysis step.
    """

    type: str
    target_columns: list[str]
    reason: str
    priority: str
    source_step: str
    prerequisites: list[str]


@dataclass(slots=True)
class VisualisationRecommendation:
    """
    Represents a deterministic visualisation recommendation.
    """

    type: str
    target_columns: list[str]
    reason: str
    priority: str
    source_step: str
    prerequisites: list[str]


@dataclass(slots=True)
class UnresolvedQuestion:
    """
    Represents a domain question that deterministic analysis cannot answer.
    """

    type: str
    target_columns: list[str]
    question: str
    reason: str
    priority: str
    source_step: str
    prerequisites: list[str]


@dataclass(slots=True)
class PriorityFinding:
    """
    Represents a traceable finding promoted from deterministic execution output.
    """

    type: str
    target_columns: list[str]
    reason: str
    priority: str
    source_step: str
    prerequisites: list[str]


@dataclass(slots=True)
class AgenticEDAResult:
    """
    Represents the complete deterministic Agentic EDA workflow output.
    """

    eda_result: EDAResult
    eda_plan: EDAPlan
    execution_result: EDAExecutionResult
    follow_up_actions: list[FollowUpAction]
    unresolved_questions: list[UnresolvedQuestion]
    recommended_visualisations: list[VisualisationRecommendation]
    priority_findings: list[PriorityFinding]
    workflow_warnings: list[str]
    deterministic_final_summary: str
    overall_status: str

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the complete workflow output to JSON-compatible structures.

        Returns:
            A nested dictionary containing only JSON-compatible values.
        """
        return to_json_compatible(self)
