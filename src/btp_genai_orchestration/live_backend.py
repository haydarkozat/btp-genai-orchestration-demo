"""LIVE backend: the SAP Generative AI Hub orchestration service.

This is the one place the SAP SDK is touched. It builds an orchestration request
from three modules the brief calls out explicitly:

  (a) a prompt template (system + user messages with ``{{?placeholder}}`` values),
  (b) grounding / context injection (retrieved chunks passed as a template value),
  (c) model config (the foundation model + parameters).

Authentication is delegated entirely to the SDK, which reads the ``AICORE_*``
service-key variables from the environment and performs the OAuth token exchange.
We never hand-roll that (per the brief).

The SDK import is lazy so MOCK mode, the test suite and CI need nothing from the
``[live]`` extra installed. This module is excluded from coverage because it only
executes against real credentials.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .backend import GenerationResult
from .config import Settings
from .models import ScoredChunk
from .prompts import SYSTEM_PROMPT, USER_TEMPLATE, format_context


class LiveBackend:
    """Calls the GenAI Hub orchestration service via the official SAP SDK."""

    name = "live"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        try:
            from gen_ai_hub.orchestration.models.config import OrchestrationConfig
            from gen_ai_hub.orchestration.models.llm import LLM
            from gen_ai_hub.orchestration.models.message import SystemMessage, UserMessage
            from gen_ai_hub.orchestration.models.template import Template, TemplateValue
            from gen_ai_hub.orchestration.service import OrchestrationService
        except ImportError as exc:  # pragma: no cover - exercised only without the extra
            raise RuntimeError(
                "LIVE mode requires the SAP SDK. Install it with:\n"
                '    pip install ".[live]"\n'
                "or run in MOCK mode by unsetting the AICORE_* environment variables."
            ) from exc

        self._template_value: Any = TemplateValue
        template = Template(
            messages=[SystemMessage(SYSTEM_PROMPT), UserMessage(USER_TEMPLATE)],
        )
        llm = LLM(name=settings.model)
        config = OrchestrationConfig(template=template, llm=llm)

        # `api_url` (the orchestration deployment URL) is optional; when omitted the
        # SDK resolves the deployment from the active resource group.
        if settings.deployment_url:
            self._service = OrchestrationService(api_url=settings.deployment_url, config=config)
        else:
            self._service = OrchestrationService(config=config)

    def generate(self, question: str, context: Sequence[ScoredChunk]) -> GenerationResult:
        context_text = format_context(context)
        result = self._service.run(
            template_values=[
                self._template_value(name="context", value=context_text),
                self._template_value(name="question", value=question),
            ]
        )
        text = result.orchestration_result.choices[0].message.content
        # All retrieved chunks were injected as grounding, so all are cited sources.
        used = list(range(1, len(context) + 1))
        return GenerationResult(text=text, used_indices=used, model=self._settings.model)
