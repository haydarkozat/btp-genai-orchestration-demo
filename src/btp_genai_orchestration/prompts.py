"""The single source of truth for the RAG prompt.

Both backends share this prompt so the LIVE orchestration call and the MOCK stub
are answering the *same* grounded question. The orchestration service renders the
``{{?placeholder}}`` syntax server-side; the mock renders it locally.
"""

from __future__ import annotations

from collections.abc import Sequence

from .models import ScoredChunk

SYSTEM_PROMPT = (
    "You are an IT operations assistant. Answer the user's question using ONLY the "
    "numbered context sections provided. If the context does not contain the answer, "
    "say so plainly instead of guessing. Be concise and actionable, and cite the "
    "sections you used with their bracketed numbers, e.g. [1]."
)

# Placeholder names match the orchestration Template values built in live_backend.
USER_TEMPLATE = "Context:\n{{?context}}\n\nQuestion: {{?question}}\n\nGrounded answer:"


def format_context(scored: Sequence[ScoredChunk]) -> str:
    """Render retrieved chunks as a numbered context block for grounding."""
    if not scored:
        return "(no relevant context found)"
    blocks = []
    for i, sc in enumerate(scored, start=1):
        blocks.append(f"[{i}] ({sc.chunk.chunk_id} — {sc.chunk.title})\n{sc.chunk.text}")
    return "\n\n".join(blocks)


def render_user_message(question: str, context: str) -> str:
    """Local equivalent of the orchestration template substitution (used by MOCK)."""
    return USER_TEMPLATE.replace("{{?context}}", context).replace("{{?question}}", question)
