"""The RAG pipeline: retrieve -> ground -> generate -> cite.

Mode-agnostic. It is handed a backend (mock or live) and never knows or cares
which one it got — that is the whole point of the abstraction.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from .backend import LLMBackend
from .config import Settings, load_settings
from .factory import create_backend
from .models import Answer, Chunk, Citation, ScoredChunk
from .retriever import Bm25Retriever
from .store import ingest as _ingest
from .store import load_index


def run_ingest(settings: Settings | None = None) -> list[Chunk]:
    """Chunk the source runbooks and persist the index. Returns the chunks."""
    settings = settings or load_settings()
    return _ingest(settings.docs_dir, settings.index_path)


class RagPipeline:
    """Ties retrieval and a generation backend together behind one ``ask`` call."""

    def __init__(
        self,
        chunks: Sequence[Chunk],
        backend: LLMBackend,
        *,
        top_k: int = 3,
    ) -> None:
        self._retriever = Bm25Retriever(chunks)
        self._backend = backend
        self._top_k = top_k

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> RagPipeline:
        """Build a pipeline from settings: load the index and select the backend."""
        settings = settings or load_settings()
        chunks = load_index(settings.index_path)
        backend = create_backend(settings)
        return cls(chunks, backend, top_k=settings.top_k)

    def ask(self, question: str) -> Answer:
        """Answer ``question``, grounded in the retrieved runbook sections."""
        retrieved = self._retriever.retrieve(question, top_k=self._top_k)
        result = self._backend.generate(question, retrieved)
        citations = _to_citations(retrieved, result.used_indices)
        return Answer(
            question=question,
            text=result.text,
            citations=citations,
            backend=self._backend.name,
            model=result.model,
        )


def _to_citations(retrieved: Sequence[ScoredChunk], used_indices: Sequence[int]) -> list[Citation]:
    """Map the backend's 1-based used indices back to citation records.

    Falls back to citing everything that was retrieved if the backend did not
    report specific indices (e.g. the live model grounded on all of them).
    """
    indices = list(used_indices) if used_indices else list(range(1, len(retrieved) + 1))
    citations: list[Citation] = []
    for idx in indices:
        if 1 <= idx <= len(retrieved):
            sc = retrieved[idx - 1]
            citations.append(
                Citation(
                    chunk_id=sc.chunk.chunk_id,
                    title=sc.chunk.title,
                    source_path=sc.chunk.source_path,
                    score=round(sc.score, 4),
                )
            )
    return citations


def index_exists(settings: Settings | None = None) -> bool:
    settings = settings or load_settings()
    return Path(settings.index_path).is_file()
