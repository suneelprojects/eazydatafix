"""Provider contract for optional grounded narrative generation."""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from eazydatafix.models.agentic_eda_narrative import NarrativeEvidence
from eazydatafix.models.serialization import to_json_compatible


@dataclass(frozen=True, slots=True)
class GroundedNarrativeRequest:
    """A provider request containing only deterministic, citeable evidence."""

    instructions: str
    evidence: tuple[NarrativeEvidence, ...]
    workflow_fingerprint: str

    def to_dict(self) -> dict[str, object]:
        """Return the request payload in a provider-neutral JSON-ready form."""
        return {
            "instructions": self.instructions,
            "evidence": to_json_compatible(self.evidence),
            "workflow_fingerprint": self.workflow_fingerprint,
        }


@runtime_checkable
class NarrativeProvider(Protocol):
    """Produces a JSON narrative response for a deterministic evidence request."""

    name: str

    def generate(self, request: GroundedNarrativeRequest) -> str:
        """Return a JSON object that conforms to the supplied instructions."""
