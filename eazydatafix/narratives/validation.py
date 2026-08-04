"""Deterministic integrity checks for optional Agentic EDA narratives."""

import hashlib
import json
import re
from collections.abc import Mapping, Sequence

from eazydatafix.models.agentic_eda_narrative import NarrativeEvidence
from eazydatafix.models.agentic_eda_result import AgenticEDAResult

_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_-]*|[-+]?\d+(?:\.\d+)?%?")
_NUMBER_PATTERN = re.compile(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?%?")
_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "before",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "were",
    "with",
}
_CAUSAL_MARKERS = {"because", "cause", "caused", "causes", "due", "led", "resulted"}


def workflow_fingerprint(workflow: AgenticEDAResult) -> str:
    """Return a stable SHA-256 fingerprint of a complete workflow result."""
    content = json.dumps(
        workflow.to_dict(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()}"


def validate_claim_grounding(
    *,
    text: str,
    evidence_ids: Sequence[str],
    evidence_by_id: Mapping[str, NarrativeEvidence],
    field_name: str,
) -> None:
    """Reject claims without deterministic lexical support from cited evidence.

    This guard catches invented numbers, unsupported causal language, and claims
    whose meaningful vocabulary is mostly absent from their cited evidence. It
    is deliberately conservative and is not a semantic proof of truth.
    """
    cited_text = " ".join(evidence_by_id[item].content for item in evidence_ids)
    claim_numbers = set(_NUMBER_PATTERN.findall(text))
    evidence_numbers = set(_NUMBER_PATTERN.findall(cited_text))
    unsupported_numbers = sorted(claim_numbers - evidence_numbers)

    if unsupported_numbers:
        raise ValueError(
            f"provider narrative field '{field_name}' contains number(s) absent "
            "from cited evidence: " + ", ".join(unsupported_numbers)
        )

    claim_tokens = _content_tokens(text)
    evidence_tokens = _content_tokens(cited_text)
    causal_tokens = claim_tokens & _CAUSAL_MARKERS

    if causal_tokens and not causal_tokens.intersection(evidence_tokens):
        raise ValueError(
            f"provider narrative field '{field_name}' introduces unsupported " "causal language."
        )

    if not claim_tokens:
        raise ValueError(
            f"provider narrative field '{field_name}' has no meaningful "
            "evidence-supported content."
        )

    supported_tokens = claim_tokens.intersection(evidence_tokens)
    required_count = min(2, len(claim_tokens))
    support_ratio = len(supported_tokens) / len(claim_tokens)

    if len(supported_tokens) < required_count or support_ratio < 0.5:
        raise ValueError(
            f"provider narrative field '{field_name}' is not sufficiently "
            "supported by its cited evidence."
        )


def _content_tokens(value: str) -> set[str]:
    return {
        token.lower() for token in _TOKEN_PATTERN.findall(value) if token.lower() not in _STOP_WORDS
    }
