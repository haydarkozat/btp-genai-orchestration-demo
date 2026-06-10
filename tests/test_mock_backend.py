from __future__ import annotations

from btp_genai_orchestration.backend import LLMBackend
from btp_genai_orchestration.mock_backend import MockBackend
from btp_genai_orchestration.models import Chunk, ScoredChunk


def _sc(chunk_id: str, title: str, text: str, score: float) -> ScoredChunk:
    return ScoredChunk(Chunk(chunk_id, chunk_id.split("#")[0], title, text, "x.md"), score)


def test_mock_backend_satisfies_protocol() -> None:
    assert isinstance(MockBackend(), LLMBackend)


def test_generate_uses_top_chunk_steps() -> None:
    ctx = [
        _sc("t#1", "Reset", "1. power off\n2. hold volume down\n3. erase all data", 0.9),
        _sc("t#2", "Verify", "confirm the device is compliant", 0.4),
    ]
    result = MockBackend().generate("how do I reset", ctx)
    assert "Reset" in result.text
    assert "power off" in result.text
    assert result.used_indices == [1, 2]
    assert result.model is None


def test_generate_with_single_chunk_cites_only_first() -> None:
    ctx = [_sc("t#1", "Reset", "just do the thing", 0.9)]
    result = MockBackend().generate("q", ctx)
    assert result.used_indices == [1]


def test_generate_no_context_is_honest() -> None:
    result = MockBackend().generate("q", [])
    assert result.used_indices == []
    assert "couldn't find" in result.text.lower()


def test_generate_falls_back_to_prose_sentences() -> None:
    ctx = [_sc("p#1", "Prose", "First sentence here. Second sentence here. Third one.", 0.5)]
    result = MockBackend().generate("q", ctx)
    assert "First sentence here" in result.text
