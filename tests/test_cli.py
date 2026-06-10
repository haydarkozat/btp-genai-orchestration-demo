from __future__ import annotations

import contextlib
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from btp_genai_orchestration.cli import app

runner = CliRunner()


def _combined(result: Any) -> str:
    """Stdout plus stderr, robust across Click versions (which differ on capture)."""
    text: str = result.output or ""
    with contextlib.suppress(ValueError):
        text += result.stderr or ""  # raises if stderr was mixed into output
    return text


@pytest.fixture
def cli_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    docs = Path(__file__).resolve().parents[1] / "data" / "runbooks"
    index = tmp_path / "index.json"
    monkeypatch.setenv("RAG_DOCS_DIR", str(docs))
    monkeypatch.setenv("RAG_INDEX_PATH", str(index))
    return index


def test_ingest_then_ask_end_to_end(cli_env: Path) -> None:
    ingest_result = runner.invoke(app, ["ingest"])
    assert ingest_result.exit_code == 0, ingest_result.output
    assert "Ingested" in ingest_result.output
    assert cli_env.is_file()

    ask_result = runner.invoke(app, ["ask", "How do I reset a student tablet?"])
    assert ask_result.exit_code == 0, ask_result.output
    assert "Sources:" in ask_result.output
    assert "tablet-reset" in ask_result.output
    assert "backend: mock" in ask_result.output


def test_ask_without_index_fails_cleanly(cli_env: Path) -> None:
    result = runner.invoke(app, ["ask", "anything"])
    assert result.exit_code == 1
    assert "demo ingest" in _combined(result)


def test_info_reports_mock_backend(cli_env: Path) -> None:
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "resolved backend:   mock" in result.output


def test_help_lists_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "ingest" in result.output
    assert "ask" in result.output


def test_no_args_shows_help_and_exits_nonzero() -> None:
    # no_args_is_help prints help and exits with the standard usage code (2).
    result = runner.invoke(app, [])
    assert result.exit_code == 2
    assert "ingest" in _combined(result)
