"""A small, dependency-free BM25 keyword retriever.

Deterministic and fully offline — the local stand-in for the vector / keyword search
that a HANA Cloud vector engine or the orchestration grounding module performs in
production. Retrieval is shared by *both* backends so citations are identical and
testable regardless of mode.

BM25 (Okapi) is used rather than plain TF-IDF cosine because its tunable length
normalization (``b``) stops long step-by-step sections from being unfairly demoted —
exactly the runbook sections a "how do I..." question wants.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Iterable

from .models import Chunk, ScoredChunk

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Section headings are high-signal, so their terms are weighted up by repetition
# when building the index (a lightweight stand-in for field-boosting in a real
# search engine).
_TITLE_WEIGHT = 2

# A short stopword list, removed from both index and query terms so that a query
# made only of common words (e.g. "what is the ... of a ...") doesn't spuriously
# match — it should fall through to an honest "not found" answer instead.
_STOPWORDS = frozenset(
    {
        "a", "an", "and", "are", "as", "at", "be", "but", "by", "do", "does",
        "for", "from", "how", "i", "if", "in", "into", "is", "it", "of", "on",
        "or", "so", "that", "the", "their", "then", "there", "these", "this",
        "to", "was", "what", "when", "where", "which", "who", "why", "with",
        "you", "your",
    }
)  # fmt: skip


def tokenize(text: str) -> list[str]:
    """Lowercase, split on non-alphanumerics. Tiny but sufficient for the demo."""
    return _TOKEN_RE.findall(text.lower())


def _terms(text: str) -> list[str]:
    """Content terms only: tokenized with stopwords removed."""
    return [token for token in tokenize(text) if token not in _STOPWORDS]


class Bm25Retriever:
    """Ranks chunks against a query with the Okapi BM25 scoring function."""

    def __init__(self, chunks: Iterable[Chunk], *, k1: float = 1.5, b: float = 0.75) -> None:
        self._chunks: list[Chunk] = list(chunks)
        self._k1 = k1
        self._b = b
        self._docs: list[Counter[str]] = []
        self._doc_len: list[int] = []
        self._idf: dict[str, float] = {}
        self._avgdl: float = 0.0
        self._fit()

    def _fit(self) -> None:
        n_docs = len(self._chunks)
        if n_docs == 0:
            return

        doc_freq: Counter[str] = Counter()
        for chunk in self._chunks:
            tokens = _terms(chunk.title) * _TITLE_WEIGHT + _terms(chunk.text)
            counts = Counter(tokens)
            self._docs.append(counts)
            self._doc_len.append(len(tokens))
            doc_freq.update(counts.keys())

        self._avgdl = sum(self._doc_len) / n_docs
        # BM25 idf in its always-non-negative form, so common terms never score < 0.
        self._idf = {
            term: math.log(1 + (n_docs - df + 0.5) / (df + 0.5)) for term, df in doc_freq.items()
        }

    def retrieve(self, query: str, top_k: int = 3) -> list[ScoredChunk]:
        """Return the ``top_k`` highest-scoring chunks (score > 0), best first."""
        query_terms = _terms(query)
        scored: list[ScoredChunk] = []
        for chunk, counts, dl in zip(self._chunks, self._docs, self._doc_len, strict=True):
            score = self._score(query_terms, counts, dl)
            if score > 0.0:
                scored.append(ScoredChunk(chunk=chunk, score=score))
        # Sort by score desc, then chunk_id for a stable, reproducible ordering.
        scored.sort(key=lambda sc: (-sc.score, sc.chunk.chunk_id))
        return scored[:top_k]

    def _score(self, query_terms: list[str], counts: Counter[str], dl: int) -> float:
        score = 0.0
        norm = self._k1 * (1 - self._b + self._b * dl / self._avgdl) if self._avgdl else self._k1
        for term in query_terms:
            freq = counts.get(term, 0)
            if freq == 0:
                continue
            score += self._idf.get(term, 0.0) * (freq * (self._k1 + 1)) / (freq + norm)
        return score
