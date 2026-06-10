from __future__ import annotations

from pathlib import Path

from btp_genai_orchestration.models import Chunk
from btp_genai_orchestration.retriever import Bm25Retriever, tokenize
from btp_genai_orchestration.store import build_index


def test_tokenize_lowercases_and_splits() -> None:
    assert tokenize("Reset the Tablet!") == ["reset", "the", "tablet"]


def test_retrieve_ranks_relevant_chunk_first(chunks: list[Chunk]) -> None:
    retriever = Bm25Retriever(chunks)
    results = retriever.retrieve("how do I reset a student tablet", top_k=3)
    assert results
    assert results[0].chunk.chunk_id == "a#1"


def test_retrieve_respects_top_k(chunks: list[Chunk]) -> None:
    retriever = Bm25Retriever(chunks)
    results = retriever.retrieve("vpn printer tablet", top_k=2)
    assert len(results) <= 2


def test_retrieve_no_match_returns_empty(chunks: list[Chunk]) -> None:
    retriever = Bm25Retriever(chunks)
    assert retriever.retrieve("xyzzy quux nonexistentword") == []


def test_stopword_only_query_returns_empty() -> None:
    docs = Path(__file__).resolve().parents[1] / "data" / "runbooks"
    retriever = Bm25Retriever(build_index(docs))
    # No content terms -> no spurious match on common words.
    assert retriever.retrieve("what is the of a an") == []


def test_retrieve_scores_sorted_descending(chunks: list[Chunk]) -> None:
    retriever = Bm25Retriever(chunks)
    results = retriever.retrieve("vpn client mfa sign", top_k=3)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
    assert results[0].chunk.chunk_id == "b#1"


def test_retriever_handles_empty_corpus() -> None:
    retriever = Bm25Retriever([])
    assert retriever.retrieve("anything") == []


def test_bm25_surfaces_action_section_on_real_runbooks() -> None:
    docs = Path(__file__).resolve().parents[1] / "data" / "runbooks"
    retriever = Bm25Retriever(build_index(docs))
    results = retriever.retrieve("printer jobs stuck in the print queue", top_k=3)
    # The troubleshooting section, not the document intro, should rank first.
    assert results[0].chunk.title == "Jobs stuck in the print queue"
