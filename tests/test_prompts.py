from __future__ import annotations

from btp_genai_orchestration.models import Chunk, ScoredChunk
from btp_genai_orchestration.prompts import (
    USER_TEMPLATE,
    format_context,
    render_user_message,
)


def _sc(chunk_id: str, title: str, text: str) -> ScoredChunk:
    return ScoredChunk(Chunk(chunk_id, "d", title, text, "d.md"), 0.5)


def test_format_context_numbers_and_labels_chunks() -> None:
    out = format_context([_sc("a#1", "Reset", "step one"), _sc("a#2", "Verify", "step two")])
    assert "[1] (a#1 — Reset)" in out
    assert "[2] (a#2 — Verify)" in out
    assert "step one" in out


def test_format_context_empty_is_explicit() -> None:
    assert "no relevant context" in format_context([])


def test_render_user_message_substitutes_placeholders() -> None:
    rendered = render_user_message("How do I reset?", "[1] context here")
    assert "{{?context}}" not in rendered
    assert "{{?question}}" not in rendered
    assert "How do I reset?" in rendered
    assert "[1] context here" in rendered


def test_user_template_declares_both_placeholders() -> None:
    assert "{{?context}}" in USER_TEMPLATE
    assert "{{?question}}" in USER_TEMPLATE
