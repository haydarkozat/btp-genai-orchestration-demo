"""LIVE integration tests — hit the real GenAI Hub orchestration service.

The whole module is skipped unless real AI Core credentials are present in the
environment AND the SAP SDK ([live] extra) is importable. That is how the suite
stays green in CI / on any machine with zero credentials.

Run them explicitly with credentials in your environment:
    pytest -m live
"""

from __future__ import annotations

import importlib.util
import os

import pytest

from btp_genai_orchestration.config import AICORE_ENV_VARS, load_settings
from btp_genai_orchestration.factory import create_backend
from btp_genai_orchestration.pipeline import RagPipeline
from btp_genai_orchestration.store import build_index

_HAS_CREDENTIALS = all(os.environ.get(name) for name in AICORE_ENV_VARS)
_HAS_SDK = importlib.util.find_spec("gen_ai_hub") is not None

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        not (_HAS_CREDENTIALS and _HAS_SDK),
        reason="LIVE tests need AICORE_* credentials and the [live] extra installed",
    ),
]


def test_live_ask_reaches_orchestration() -> None:
    settings = load_settings()
    assert settings.use_live is True

    chunks = build_index(settings.docs_dir)
    pipeline = RagPipeline(chunks, create_backend(settings), top_k=settings.top_k)
    answer = pipeline.ask("How do I reset a student tablet?")

    assert answer.backend == "live"
    assert answer.model == settings.model
    assert answer.text.strip()
    assert answer.citations, "live answer must still cite its grounding sources"
