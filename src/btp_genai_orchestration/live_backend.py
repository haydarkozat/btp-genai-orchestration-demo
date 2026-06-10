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
``[live]`` extra installed. Request construction is factored into
:func:`build_orchestration_config` / :func:`build_template_values` so it can be
exercised — without sending anything or needing credentials — by the SDK-contract
test (``tests/test_live_contract.py``), which catches SDK API drift in CI.

This module is excluded from coverage because the network call only runs against
real credentials.
"""

from __future__ import annotations

from collections.abc import Sequence
from types import SimpleNamespace
from typing import Any

from .backend import GenerationResult
from .config import Settings
from .models import ScoredChunk
from .prompts import SYSTEM_PROMPT, USER_TEMPLATE, format_context

_MISSING_SDK_MESSAGE = (
    "LIVE mode requires the SAP SDK. Install it with:\n"
    '    pip install ".[live]"\n'
    "or run in MOCK mode by unsetting the AICORE_* environment variables."
)


def _load_sdk() -> Any:
    """Import the orchestration SDK classes, or raise a friendly RuntimeError.

    Returns a namespace of the classes used below. Kept in one place so both the
    request builders and the service wiring import the exact same symbols.
    """
    try:
        from gen_ai_hub.orchestration.models.config import OrchestrationConfig
        from gen_ai_hub.orchestration.models.llm import LLM
        from gen_ai_hub.orchestration.models.message import SystemMessage, UserMessage
        from gen_ai_hub.orchestration.models.template import Template, TemplateValue
        from gen_ai_hub.orchestration.service import OrchestrationService
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise RuntimeError(_MISSING_SDK_MESSAGE) from exc

    return SimpleNamespace(
        SystemMessage=SystemMessage,
        UserMessage=UserMessage,
        Template=Template,
        TemplateValue=TemplateValue,
        LLM=LLM,
        OrchestrationConfig=OrchestrationConfig,
        OrchestrationService=OrchestrationService,
    )


def build_orchestration_config(model: str) -> Any:
    """Build the orchestration request config (prompt template + model).

    Pure construction — no network, no credentials. This is the "request object"
    the LIVE backend would send; building it validates that our use of the SDK
    (Template/SystemMessage/UserMessage/LLM/OrchestrationConfig) still matches the
    installed package.
    """
    sdk = _load_sdk()
    template = sdk.Template(
        messages=[sdk.SystemMessage(SYSTEM_PROMPT), sdk.UserMessage(USER_TEMPLATE)],
    )
    return sdk.OrchestrationConfig(template=template, llm=sdk.LLM(name=model))


def build_template_values(question: str, context_text: str) -> Any:
    """Build the grounding/question template values for a run. No network."""
    sdk = _load_sdk()
    return [
        sdk.TemplateValue(name="context", value=context_text),
        sdk.TemplateValue(name="question", value=question),
    ]


class LiveBackend:
    """Calls the GenAI Hub orchestration service via the official SAP SDK."""

    name = "live"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        sdk = _load_sdk()
        config = build_orchestration_config(settings.model)

        # `api_url` (the orchestration deployment URL) is optional; when omitted the
        # SDK resolves the deployment from the active resource group.
        if settings.deployment_url:
            self._service = sdk.OrchestrationService(api_url=settings.deployment_url, config=config)
        else:
            self._service = sdk.OrchestrationService(config=config)

    def generate(self, question: str, context: Sequence[ScoredChunk]) -> GenerationResult:
        context_text = format_context(context)
        result = self._service.run(template_values=build_template_values(question, context_text))
        text = result.orchestration_result.choices[0].message.content
        # All retrieved chunks were injected as grounding, so all are cited sources.
        used = list(range(1, len(context) + 1))
        return GenerationResult(text=text, used_indices=used, model=self._settings.model)
