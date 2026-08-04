"""Grounded narrative orchestration that never changes deterministic results."""

import json
from collections.abc import Sequence
from dataclasses import asdict
from typing import Any

from eazydatafix.models.agentic_eda_narrative import (
    AgenticEDANarrative,
    NarrativeClaim,
    NarrativeEvidence,
)
from eazydatafix.models.agentic_eda_narrative_config import AgenticEDANarrativeConfig
from eazydatafix.models.agentic_eda_result import AgenticEDAResult
from eazydatafix.narratives.provider import GroundedNarrativeRequest, NarrativeProvider

_TITLE = "Grounded Agentic EDA Narrative"
_GROUNDING_NOTICE = (
    "This optional AI narrative was generated only from the cited deterministic "
    "EazyDataFix workflow evidence. It does not alter calculated metrics, findings, "
    "or recommendations."
)
_INSTRUCTIONS = """You write a concise business-facing narrative from supplied EazyDataFix evidence.
Use only the supplied evidence. Do not infer causes, values, trends, or recommendations that
are absent from it. You do not receive the raw dataset. Return JSON only with these exact keys:
summary, findings, next_steps, unresolved_questions.
Each value is a claim object or a list of claim objects. A claim object has exactly:
text (a non-empty string) and evidence_ids (a non-empty array of unique supplied evidence IDs).
The summary must be one claim. Findings, next_steps, and unresolved_questions must be arrays.
Every claim must cite the evidence IDs that support it. Do not include markdown fences or prose
outside the JSON object. Keep the narrative factual and concise."""


class GroundedNarrativeEngine:
    """Build and validate an optional narrative from an existing EDA workflow."""

    def generate(
        self,
        workflow: AgenticEDAResult,
        provider: NarrativeProvider,
        config: AgenticEDANarrativeConfig | None = None,
    ) -> AgenticEDANarrative:
        """Generate a cited narrative without rerunning or modifying the workflow.

        Args:
            workflow: A completed deterministic Agentic EDA workflow.
            provider: An adapter that accepts only the prepared evidence request.
            config: Optional deterministic evidence limits.

        Returns:
            A validated narrative whose every generated claim cites known evidence.
        """
        if not isinstance(workflow, AgenticEDAResult):
            raise TypeError("workflow must be an AgenticEDAResult.")

        if (
            not isinstance(getattr(provider, "name", None), str)
            or not provider.name.strip()
            or not callable(getattr(provider, "generate", None))
        ):
            raise TypeError("provider must implement name and generate(request).")

        selected_config = self._validate_config(config)
        evidence = self._build_evidence(workflow, selected_config)
        request = GroundedNarrativeRequest(instructions=_INSTRUCTIONS, evidence=evidence)
        response = provider.generate(request)
        payload = self._parse_response(response)
        available_ids = {item.id for item in evidence}

        return AgenticEDANarrative(
            title=_TITLE,
            summary=self._claim(payload["summary"], "summary", available_ids),
            findings=self._claims(
                payload["findings"],
                "findings",
                available_ids,
                selected_config.max_findings,
            ),
            next_steps=self._claims(
                payload["next_steps"],
                "next_steps",
                available_ids,
                selected_config.max_next_steps,
            ),
            unresolved_questions=self._claims(
                payload["unresolved_questions"],
                "unresolved_questions",
                available_ids,
                selected_config.max_unresolved_questions,
            ),
            evidence=evidence,
            provider_name=provider.name,
            grounding_notice=_GROUNDING_NOTICE,
        )

    @staticmethod
    def _validate_config(
        config: AgenticEDANarrativeConfig | None,
    ) -> AgenticEDANarrativeConfig:
        if config is None:
            return AgenticEDANarrativeConfig()

        if not isinstance(config, AgenticEDANarrativeConfig):
            raise TypeError("config must be an AgenticEDANarrativeConfig or None.")

        return config

    @staticmethod
    def _build_evidence(
        workflow: AgenticEDAResult,
        config: AgenticEDANarrativeConfig,
    ) -> list[NarrativeEvidence]:
        evidence = [
            NarrativeEvidence(
                id="workflow-summary",
                source_type="workflow_summary",
                source_step=None,
                content=workflow.deterministic_final_summary,
            ),
            NarrativeEvidence(
                id="dataset-profile",
                source_type="dataset_profile",
                source_step=None,
                content=(
                    f"Dataset shape: {workflow.eda_result.shape[0]} rows and "
                    f"{workflow.eda_result.shape[1]} columns. Overall workflow status: "
                    f"{workflow.overall_status}."
                ),
            ),
        ]
        evidence.extend(
            GroundedNarrativeEngine._records(
                "finding",
                workflow.priority_findings[: config.max_findings],
            )
        )
        evidence.extend(
            GroundedNarrativeEngine._records(
                "next-step",
                workflow.follow_up_actions[: config.max_next_steps],
            )
        )
        evidence.extend(
            GroundedNarrativeEngine._records(
                "unresolved-question",
                workflow.unresolved_questions[: config.max_unresolved_questions],
            )
        )

        if config.include_workflow_warnings:
            for index, warning in enumerate(workflow.workflow_warnings, start=1):
                evidence.append(
                    NarrativeEvidence(
                        id=f"warning-{index:02d}",
                        source_type="workflow_warning",
                        source_step=None,
                        content=warning,
                    )
                )

        return evidence

    @staticmethod
    def _records(
        source_type: str,
        records: Sequence[Any],
    ) -> list[NarrativeEvidence]:
        return [
            NarrativeEvidence(
                id=f"{source_type}-{index:02d}",
                source_type=source_type,
                source_step=getattr(record, "source_step", None),
                content=json.dumps(asdict(record), sort_keys=True, ensure_ascii=False),
            )
            for index, record in enumerate(records, start=1)
        ]

    @staticmethod
    def _parse_response(response: str) -> dict[str, Any]:
        if not isinstance(response, str):
            raise TypeError("provider.generate() must return a JSON string.")

        try:
            payload = json.loads(response)
        except json.JSONDecodeError as exc:
            raise ValueError("provider returned invalid narrative JSON.") from exc

        if not isinstance(payload, dict):
            raise ValueError("provider narrative response must be a JSON object.")

        required = {"summary", "findings", "next_steps", "unresolved_questions"}
        if set(payload) != required:
            raise ValueError(
                "provider narrative response must contain exactly: " + ", ".join(sorted(required))
            )

        return payload

    @staticmethod
    def _claims(
        value: Any,
        field_name: str,
        available_ids: set[str],
        maximum: int,
    ) -> list[NarrativeClaim]:
        if not isinstance(value, list):
            raise ValueError(f"provider narrative field '{field_name}' must be an array.")

        if len(value) > maximum:
            raise ValueError(
                f"provider narrative field '{field_name}' exceeds the configured "
                f"limit of {maximum}."
            )

        return [
            GroundedNarrativeEngine._claim(item, f"{field_name}[{index}]", available_ids)
            for index, item in enumerate(value)
        ]

    @staticmethod
    def _claim(
        value: Any,
        field_name: str,
        available_ids: set[str],
    ) -> NarrativeClaim:
        if not isinstance(value, dict) or set(value) != {"text", "evidence_ids"}:
            raise ValueError(
                f"provider narrative field '{field_name}' must contain exactly "
                "text and evidence_ids."
            )

        text = value["text"]
        evidence_ids = value["evidence_ids"]

        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"provider narrative field '{field_name}.text' must be non-empty.")

        if isinstance(evidence_ids, (str, bytes)) or not isinstance(evidence_ids, list):
            raise ValueError(
                f"provider narrative field '{field_name}.evidence_ids' must be an array."
            )

        if not evidence_ids or any(not isinstance(item, str) or not item for item in evidence_ids):
            raise ValueError(
                f"provider narrative field '{field_name}.evidence_ids' must contain ID strings."
            )

        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError(f"provider narrative field '{field_name}' has duplicate evidence IDs.")

        unknown_ids = [item for item in evidence_ids if item not in available_ids]
        if unknown_ids:
            raise ValueError(
                f"provider narrative field '{field_name}' cites unknown evidence ID(s): "
                + ", ".join(unknown_ids)
            )

        return NarrativeClaim(text=text.strip(), evidence_ids=list(evidence_ids))
