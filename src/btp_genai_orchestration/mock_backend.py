"""Offline stub backend: deterministic, coherent, zero credentials, zero network.

Implements the same :class:`LLMBackend` protocol as the live orchestration call so
the CLI, tests and demo run with nothing installed but the base package. The
"generation" is extractive: it stitches together the most salient lines from the
retrieved context and cites them — canned, but coherent and grounded.

For a "how do I..." question, the most useful grounded section is usually the one
with actual steps, which is not always the single top-ranked hit. So the stub
answers from the highest-ranked section that *contains* procedural steps (falling
back to the top hit), and still cites the top-ranked section as a related source.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from .backend import GenerationResult
from .models import ScoredChunk

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_STEP_RE = re.compile(r"^(\d+[.)]|[-*•])\s+")
_MD_EMPHASIS = re.compile(r"[*`]+")


def _is_step(line: str) -> bool:
    return bool(_STEP_RE.match(line.strip()))


def _has_steps(text: str) -> bool:
    return any(_is_step(line) for line in text.splitlines())


def _clean(text: str) -> str:
    return _MD_EMPHASIS.sub("", text).strip()


def _salient_lines(text: str, limit: int = 4) -> list[str]:
    """Pull out the most instruction-like lines: numbered/bulleted steps first.

    Wrapped step continuations (indented lines following a step) are joined back
    onto their step so the extracted text is not truncated mid-sentence.
    """
    steps: list[str] = []
    prose: list[str] = []
    current: str | None = None

    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            if current is not None:
                steps.append(current)
                current = None
            continue
        if _is_step(stripped):
            if current is not None:
                steps.append(current)
            current = _clean(_STEP_RE.sub("", stripped))
        elif current is not None and raw[:1] in " \t":
            current = f"{current} {_clean(stripped)}"
        else:
            if current is not None:
                steps.append(current)
                current = None
            prose.append(_clean(stripped))

    if current is not None:
        steps.append(current)

    if steps:
        return steps[:limit]
    # Fall back to the first few sentences of prose.
    joined = " ".join(prose)
    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(joined) if s.strip()]
    return sentences[:limit]


class MockBackend:
    """A canned-but-coherent generator over the retrieved context."""

    name = "mock"

    def generate(self, question: str, context: Sequence[ScoredChunk]) -> GenerationResult:
        if not context:
            return GenerationResult(
                text=(
                    "I couldn't find anything about that in the ingested runbooks. "
                    "Try rephrasing, or ingest more documentation."
                ),
                used_indices=[],
                model=None,
            )

        primary_idx = self._pick_primary(context)
        # Citation order: primary first, then the top-ranked section if different.
        order = [primary_idx]
        if len(context) > 1:
            order.append(0 if primary_idx != 0 else 1)

        primary = context[primary_idx]
        lines = _salient_lines(primary.chunk.text)
        body = [f'Based on the "{primary.chunk.title}" runbook [1]:']
        if lines:
            body.extend(f"  {i}. {line}" for i, line in enumerate(lines, start=1))
        else:
            body.append(f"  {primary.chunk.text.strip()}")

        if len(order) > 1:
            secondary = context[order[1]]
            body.append(f'See also "{secondary.chunk.title}" [2] for related context.')

        # used_indices are 1-based positions into `context`, in citation order, so the
        # inline [1]/[2] markers line up with the rendered Sources list.
        used_indices = [idx + 1 for idx in order]
        return GenerationResult(text="\n".join(body), used_indices=used_indices, model=None)

    @staticmethod
    def _pick_primary(context: Sequence[ScoredChunk]) -> int:
        """Highest-ranked chunk that has procedural steps, else the top hit."""
        for i, sc in enumerate(context):
            if _has_steps(sc.chunk.text):
                return i
        return 0
