import json
from pathlib import Path

import pandas as pd
import pytest

import eazydatafix as edf
from eazydatafix.models.agentic_eda_narrative import (
    AgenticEDANarrative,
    NarrativeEvidence,
)
from eazydatafix.narratives import GroundedNarrativeEngine, OpenAINarrativeProvider


class _NarrativeProvider:
    name = "test-provider"

    def __init__(self, response: dict[str, object] | None = None) -> None:
        self.request = None
        self._response = response

    def generate(self, request) -> str:
        self.request = request

        if self._response is not None:
            return json.dumps(self._response)

        evidence = {item.id: item.content for item in request.evidence}
        return json.dumps(
            {
                "summary": {
                    "text": evidence["dataset-profile"],
                    "evidence_ids": ["dataset-profile"],
                },
                "findings": [
                    {
                        "text": evidence["finding-01"],
                        "evidence_ids": ["finding-01"],
                    }
                ],
                "next_steps": [
                    {
                        "text": evidence["next-step-01"],
                        "evidence_ids": ["next-step-01"],
                    }
                ],
                "unresolved_questions": [
                    {
                        "text": evidence["unresolved-question-01"],
                        "evidence_ids": ["unresolved-question-01"],
                    }
                ],
            }
        )


def _workflow() -> object:
    return edf.run_agentic_eda(
        pd.DataFrame(
            {
                "customer_id": list(range(10)),
                "amount": [1.0, 2.0, None, 4.0, 100.0, 2.0, 3.0, 4.0, 5.0, 6.0],
                "target": ["yes"] * 8 + ["no"] * 2,
            }
        )
    )


def test_grounded_narrative_is_public_and_does_not_change_workflow() -> None:
    workflow = _workflow()
    original = workflow.to_dict()
    provider = _NarrativeProvider()

    narrative = edf.generate_agentic_eda_narrative(workflow, provider)

    assert callable(edf.generate_agentic_eda_narrative)
    assert "generate_agentic_eda_narrative" in edf.__all__
    assert edf.AgenticEDANarrative is AgenticEDANarrative
    assert narrative.provider_name == "test-provider"
    assert narrative.summary.evidence_ids == ("dataset-profile",)
    assert narrative.workflow_fingerprint.startswith("sha256:")
    assert workflow.to_dict() == original


def test_provider_receives_only_compact_deterministic_evidence() -> None:
    workflow = _workflow()
    provider = _NarrativeProvider()

    edf.generate_agentic_eda_narrative(workflow, provider)

    assert provider.request is not None
    evidence = provider.request.evidence
    assert isinstance(evidence, tuple)
    assert [item.id for item in evidence[:2]] == ["workflow-summary", "dataset-profile"]
    assert any(item.id == "finding-01" for item in evidence)
    assert all('amount": [' not in item.content for item in evidence)
    assert "raw dataset" in provider.request.instructions.lower()


def test_semantically_unanchored_claim_is_rejected() -> None:
    response = {
        "summary": {
            "text": "Revenue doubled because the marketing campaign succeeded.",
            "evidence_ids": ["dataset-profile"],
        },
        "findings": [],
        "next_steps": [],
        "unresolved_questions": [],
    }

    with pytest.raises(ValueError, match="unsupported causal language|not sufficiently supported"):
        edf.generate_agentic_eda_narrative(_workflow(), _NarrativeProvider(response))


class _EvidenceMutatingProvider:
    name = "mutating-provider"

    def generate(self, request) -> str:
        invented = NarrativeEvidence(
            id="invented",
            source_type="invented",
            source_step=None,
            content="Invented revenue evidence.",
        )
        object.__setattr__(request, "evidence", request.evidence + (invented,))
        return json.dumps(
            {
                "summary": {
                    "text": "Invented revenue evidence.",
                    "evidence_ids": ["invented"],
                },
                "findings": [],
                "next_steps": [],
                "unresolved_questions": [],
            }
        )


def test_provider_cannot_expand_the_valid_evidence_id_snapshot() -> None:
    with pytest.raises(ValueError, match="unknown evidence ID"):
        edf.generate_agentic_eda_narrative(_workflow(), _EvidenceMutatingProvider())


@pytest.mark.parametrize(
    "response, error",
    [
        (
            {
                "summary": {"text": "Uncited", "evidence_ids": []},
                "findings": [],
                "next_steps": [],
                "unresolved_questions": [],
            },
            "must contain ID strings",
        ),
        (
            {
                "summary": {"text": "Unknown", "evidence_ids": ["not-real"]},
                "findings": [],
                "next_steps": [],
                "unresolved_questions": [],
            },
            "unknown evidence ID",
        ),
        (
            {
                "summary": {"text": "Supported", "evidence_ids": ["workflow-summary"]},
                "findings": [],
                "next_steps": [],
            },
            "contain exactly",
        ),
    ],
)
def test_uncited_or_invalid_narratives_are_rejected(
    response: dict[str, object],
    error: str,
) -> None:
    with pytest.raises(ValueError, match=error):
        edf.generate_agentic_eda_narrative(_workflow(), _NarrativeProvider(response))


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("max_findings", -1, ValueError),
        ("max_next_steps", True, TypeError),
        ("max_unresolved_questions", 1.5, TypeError),
        ("include_workflow_warnings", "yes", TypeError),
    ],
)
def test_narrative_config_validation(field: str, value: object, error: type[Exception]) -> None:
    with pytest.raises(error):
        edf.AgenticEDANarrativeConfig(**{field: value})


def test_report_export_includes_optional_grounded_narrative(tmp_path: Path) -> None:
    workflow = _workflow()
    narrative = edf.generate_agentic_eda_narrative(workflow, _NarrativeProvider())

    result = edf.export_agentic_eda_report(
        workflow,
        output_dir=tmp_path / "report",
        formats=["html", "json", "markdown"],
        narrative=narrative,
    )
    output_directory = Path(result.output_directory)
    html = (output_directory / "agentic-eda-report.html").read_text(encoding="utf-8")
    markdown = (output_directory / "agentic-eda-report.md").read_text(encoding="utf-8")
    payload = json.loads((output_directory / "agentic-eda-report.json").read_text(encoding="utf-8"))

    assert "Grounded AI narrative" in html
    assert "Grounded AI narrative" in markdown
    assert "Evidence reference" in html
    assert "Evidence reference" in markdown
    assert "dataset-profile" in html
    assert "dataset-profile" in markdown
    assert payload["grounded_narrative"] == narrative.to_dict()
    assert payload["reproducibility_metadata"]["optional_ai_narrative_included"] is True


def test_report_rejects_narrative_from_a_different_workflow(tmp_path: Path) -> None:
    narrative = edf.generate_agentic_eda_narrative(_workflow(), _NarrativeProvider())
    different_workflow = edf.run_agentic_eda(
        pd.DataFrame({"customer_id": range(5), "amount": [1, 2, 3, 4, 5]})
    )
    output_directory = tmp_path / "mismatched-report"

    with pytest.raises(ValueError, match="different or modified"):
        edf.export_agentic_eda_report(
            different_workflow,
            output_dir=output_directory,
            narrative=narrative,
        )

    assert not output_directory.exists()


class _Response:
    output_text = json.dumps(
        {
            "summary": {"text": "Dataset shape", "evidence_ids": ["dataset-profile"]},
            "findings": [],
            "next_steps": [],
            "unresolved_questions": [],
        }
    )


class _Responses:
    def __init__(self) -> None:
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return _Response()


class _OpenAIClient:
    def __init__(self) -> None:
        self.responses = _Responses()


def test_openai_provider_uses_injected_responses_client() -> None:
    client = _OpenAIClient()
    provider = OpenAINarrativeProvider(model="test-model", client=client)
    workflow = _workflow()
    narrative = GroundedNarrativeEngine().generate(workflow, provider)

    assert narrative.summary.text == "Dataset shape"
    assert client.responses.kwargs["model"] == "test-model"
    assert "raw dataset" not in client.responses.kwargs["input"].lower()
    assert client.responses.kwargs["text"]["format"]["type"] == "json_schema"
    assert client.responses.kwargs["text"]["format"]["strict"] is True
