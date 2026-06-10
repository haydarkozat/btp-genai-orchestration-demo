"""The single abstraction the whole mode switch turns on.

`LLMBackend` is the *only* seam between MOCK and LIVE. Everything upstream — the
CLI, the pipeline, retrieval, citations — is identical in both modes. There are no
``if mock:`` branches scattered through the code; the factory picks one
implementation of this protocol and the rest of the program is none the wiser.

This is the architecture talking point: swapping a self-hosted Ollama generator
(SOUVERAEN-KI) for the SAP GenAI Hub orchestration service is a one-class change.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .models import ScoredChunk


@dataclass(frozen=True, slots=True)
class GenerationResult:
    """What a backend returns: the answer text plus which context blocks it used."""

    text: str
    """The generated answer."""
    used_indices: list[int]
    """1-based indices into the provided context that the answer relied on."""
    model: str | None = None
    """Identifier of the model that produced the answer (None for the stub)."""


@runtime_checkable
class LLMBackend(Protocol):
    """Generate a grounded answer from a question and retrieved context.

    Implementations MUST NOT perform retrieval — that is shared and happens
    upstream. They receive the already-retrieved, already-scored context and are
    responsible only for turning it into an answer.
    """

    @property
    def name(self) -> str:
        """Short backend label, e.g. ``mock`` or ``live``."""
        ...

    def generate(self, question: str, context: Sequence[ScoredChunk]) -> GenerationResult:
        """Produce an answer grounded in ``context`` for ``question``."""
        ...
