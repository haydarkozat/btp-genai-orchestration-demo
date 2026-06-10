from __future__ import annotations

from btp_genai_orchestration.models import Answer, Citation


def test_render_includes_citations_and_backend() -> None:
    answer = Answer(
        question="q",
        text="do the thing",
        citations=[Citation("a#1", "Reset", "a.md", 0.5)],
        backend="mock",
        model=None,
    )
    rendered = answer.render()
    assert "do the thing" in rendered
    assert "[1] a#1 — Reset (a.md)" in rendered
    assert "[backend: mock]" in rendered


def test_render_handles_no_citations() -> None:
    rendered = Answer(question="q", text="no idea").render()
    assert "none" in rendered.lower()


def test_render_shows_model_for_live() -> None:
    answer = Answer(question="q", text="t", backend="live", model="gpt-4o-mini")
    assert "[backend: live:gpt-4o-mini]" in answer.render()
