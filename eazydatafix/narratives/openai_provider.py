"""Optional OpenAI Responses API adapter for grounded narratives."""

import json
from typing import Any

from eazydatafix.narratives.provider import GroundedNarrativeRequest

_CLAIM_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["text", "evidence_ids"],
    "properties": {
        "text": {"type": "string"},
        "evidence_ids": {"type": "array", "items": {"type": "string"}},
    },
}
_RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["summary", "findings", "next_steps", "unresolved_questions"],
    "properties": {
        "summary": _CLAIM_SCHEMA,
        "findings": {"type": "array", "items": _CLAIM_SCHEMA},
        "next_steps": {"type": "array", "items": _CLAIM_SCHEMA},
        "unresolved_questions": {"type": "array", "items": _CLAIM_SCHEMA},
    },
}


class OpenAINarrativeProvider:
    """Generate grounded narratives with an installed OpenAI SDK client.

    Install the optional dependency with ``pip install "eazydatafix[openai]"``.
    A caller may inject an already configured OpenAI client, which keeps API-key
    handling outside EazyDataFix.
    """

    name = "openai"

    def __init__(
        self,
        model: str,
        client: Any | None = None,
    ) -> None:
        """Initialise the adapter with an explicit model and optional client."""
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model must be a non-empty string.")

        if client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise ImportError(
                    'OpenAI narrative support requires `pip install "eazydatafix[openai]"`.'
                ) from exc

            client = OpenAI()

        if not hasattr(client, "responses") or not hasattr(client.responses, "create"):
            raise TypeError("client must provide responses.create(...).")

        self._model = model.strip()
        self._client = client

    def generate(self, request: GroundedNarrativeRequest) -> str:
        """Request a JSON-only narrative using the OpenAI Responses API."""
        response = self._client.responses.create(
            model=self._model,
            instructions=request.instructions,
            input=json.dumps(
                {
                    "workflow_fingerprint": request.workflow_fingerprint,
                    "evidence": request.to_dict()["evidence"],
                },
                ensure_ascii=False,
            ),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "agentic_eda_narrative",
                    "strict": True,
                    "schema": _RESPONSE_SCHEMA,
                }
            },
        )
        output = getattr(response, "output_text", None)

        if not isinstance(output, str) or not output.strip():
            raise RuntimeError("OpenAI returned no narrative text.")

        return output
