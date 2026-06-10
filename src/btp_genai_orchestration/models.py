"""Immutable data structures shared across the pipeline.

Kept free of any backend- or SDK-specific types so the same objects flow through
both the MOCK and LIVE code paths unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Chunk:
    """A retrievable slice of a source document (one Markdown section)."""

    chunk_id: str
    """Stable identifier, e.g. ``tablet-reset#1``."""
    doc_id: str
    """Source document stem, e.g. ``tablet-reset``."""
    title: str
    """Human-readable section heading."""
    text: str
    """Body text of the section."""
    source_path: str
    """Path of the originating file, for honest provenance in citations."""


@dataclass(frozen=True, slots=True)
class ScoredChunk:
    """A chunk paired with its relevance score for a given query."""

    chunk: Chunk
    score: float


@dataclass(frozen=True, slots=True)
class Citation:
    """A source the answer was grounded on."""

    chunk_id: str
    title: str
    source_path: str
    score: float


@dataclass(frozen=True, slots=True)
class Answer:
    """The final, user-facing result of an ``ask`` call."""

    question: str
    text: str
    citations: list[Citation] = field(default_factory=list)
    backend: str = "mock"
    model: str | None = None

    def render(self) -> str:
        """Format the answer with a numbered citation list for the CLI."""
        lines = [self.text.strip(), ""]
        if self.citations:
            lines.append("Sources:")
            for i, c in enumerate(self.citations, start=1):
                lines.append(f"  [{i}] {c.chunk_id} — {c.title} ({c.source_path})")
        else:
            lines.append("Sources: (none — no matching runbook section found)")
        backend_label = self.backend if self.model is None else f"{self.backend}:{self.model}"
        lines.append("")
        lines.append(f"[backend: {backend_label}]")
        return "\n".join(lines)
