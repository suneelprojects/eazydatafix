"""Structured, cited presentation output for Agentic EDA workflows."""

from dataclasses import dataclass
from typing import Any

from eazydatafix.models.serialization import to_json_compatible


@dataclass(frozen=True, slots=True)
class NarrativeEvidence:
    """A deterministic fact that an optional narrative may cite."""

    id: str
    source_type: str
    source_step: str | None
    content: str


@dataclass(frozen=True, slots=True)
class NarrativeClaim:
    """One model-written statement with links to deterministic evidence."""

    text: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AgenticEDANarrative:
    """An optional, grounded presentation of deterministic workflow results."""

    title: str
    summary: NarrativeClaim
    findings: tuple[NarrativeClaim, ...]
    next_steps: tuple[NarrativeClaim, ...]
    unresolved_questions: tuple[NarrativeClaim, ...]
    evidence: tuple[NarrativeEvidence, ...]
    provider_name: str
    grounding_notice: str
    workflow_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        """Convert the narrative and its evidence to JSON-compatible structures."""
        return to_json_compatible(self)
