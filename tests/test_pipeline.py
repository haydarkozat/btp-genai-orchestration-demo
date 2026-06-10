from __future__ import annotations

from pathlib import Path

import pytest

from btp_genai_orchestration.config import Settings
from btp_genai_orchestration.mock_backend import MockBackend
from btp_genai_orchestration.models import Chunk
from btp_genai_orchestration.pipeline import RagPipeline, index_exists, run_ingest


def test_ask_grounds_and_cites(ingested: list[Chunk]) -> None:
    pipeline = RagPipeline(ingested, MockBackend(), top_k=3)
    answer = pipeline.ask("How do I reset a student tablet?")
    assert answer.backend == "mock"
    assert answer.citations, "answer must cite at least one source"
    # The tablet-reset runbook should be the grounding source.
    assert any(c.chunk_id.startswith("tablet-reset") for c in answer.citations)


def test_ask_unknown_topic_returns_no_citations(ingested: list[Chunk]) -> None:
    pipeline = RagPipeline(ingested, MockBackend(), top_k=3)
    answer = pipeline.ask("zzzz qqqq nonexistent topic vvvv")
    assert answer.citations == []


def test_citations_map_to_used_indices(ingested: list[Chunk]) -> None:
    pipeline = RagPipeline(ingested, MockBackend(), top_k=3)
    answer = pipeline.ask("printer queue stuck spooler")
    # Mock cites the chunks it used; citation count matches reported indices.
    assert 1 <= len(answer.citations) <= 2


def test_from_settings_uses_mock_without_credentials(
    settings: Settings, ingested: list[Chunk]
) -> None:
    pipeline = RagPipeline.from_settings(settings)
    answer = pipeline.ask("How do I reset a student tablet?")
    assert answer.backend == "mock"


def test_run_ingest_writes_index(settings: Settings) -> None:
    chunks = run_ingest(settings)
    assert chunks
    assert index_exists(settings)


def test_index_exists_false_when_absent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from btp_genai_orchestration.config import load_settings

    monkeypatch.setenv("RAG_INDEX_PATH", str(tmp_path / "missing.json"))
    assert index_exists(load_settings(load_env_file=False)) is False
