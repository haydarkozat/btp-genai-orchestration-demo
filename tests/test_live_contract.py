"""SDK contract test — catches GenAI Hub SDK API drift WITHOUT credentials.

Unlike ``test_live.py`` (which needs a real service key and network), this builds
the LIVE backend's orchestration request object locally and asserts the response
accessor chain still exists on the installed SDK. It is skipped when the ``[live]``
extra is not installed (so the default test matrix stays green), and runs in the
dedicated ``sdk-contract`` CI job where the SDK *is* installed.

If a future SDK release renames a class, kwarg, or response field we depend on,
this test fails — turning a silent LIVE-mode breakage into a red CI build.
"""

from __future__ import annotations

import importlib.util
from typing import Any

import pytest

_HAS_SDK = importlib.util.find_spec("gen_ai_hub") is not None

pytestmark = pytest.mark.skipif(not _HAS_SDK, reason="SAP SDK ([live] extra) not installed")


def test_build_orchestration_config_matches_sdk() -> None:
    from btp_genai_orchestration.live_backend import build_orchestration_config

    config = build_orchestration_config("gpt-4o-mini")
    # Constructing it at all proves Template/SystemMessage/UserMessage/LLM/
    # OrchestrationConfig still accept our arguments.
    assert type(config).__name__ == "OrchestrationConfig"


def test_build_template_values_matches_sdk() -> None:
    from btp_genai_orchestration.live_backend import build_template_values

    values = build_template_values("How do I reset a tablet?", "grounding context")
    assert [v.name for v in values] == ["context", "question"]
    assert values[0].value == "grounding context"


def test_response_accessor_chain_unchanged() -> None:
    # We read result.orchestration_result.choices[0].message.content in
    # live_backend.generate; assert every hop in that chain still exists.
    from gen_ai_hub.orchestration.models import response as r

    def fields(cls: Any) -> set[str]:
        return set(
            getattr(cls, "__fields__", None)
            or getattr(cls, "model_fields", None)
            or getattr(cls, "__annotations__", {})
        )

    assert "orchestration_result" in fields(r.OrchestrationResponse)
    assert "choices" in fields(r.LLMResult)
    assert "message" in fields(r.LLMChoice)
    assert "content" in fields(r.Message)
