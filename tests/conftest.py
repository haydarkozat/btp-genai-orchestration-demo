"""Shared fixtures. Every test runs in MOCK mode with zero credentials."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from btp_genai_orchestration.config import AICORE_ENV_VARS, Settings, load_settings
from btp_genai_orchestration.models import Chunk
from btp_genai_orchestration.store import ingest

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DOCS = REPO_ROOT / "data" / "runbooks"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Guarantee no real credentials leak into tests -> always MOCK."""
    for name in (*AICORE_ENV_VARS, "AICORE_RESOURCE_GROUP", "BACKEND_MODE"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def index_path(tmp_path: Path) -> Path:
    return tmp_path / "index.json"


@pytest.fixture
def ingested(index_path: Path) -> list[Chunk]:
    """Ingest the real sample runbooks into a temp index."""
    return ingest(SAMPLE_DOCS, index_path)


@pytest.fixture
def settings(monkeypatch: pytest.MonkeyPatch, index_path: Path) -> Settings:
    monkeypatch.setenv("RAG_INDEX_PATH", str(index_path))
    monkeypatch.setenv("RAG_DOCS_DIR", str(SAMPLE_DOCS))
    return load_settings(load_env_file=False)


@pytest.fixture
def chunks() -> Iterator[list[Chunk]]:
    """A tiny, hand-built corpus for retrieval unit tests."""
    yield [
        Chunk(
            "a#1", "a", "Reset a tablet", "factory reset the student tablet via MDM wipe", "a.md"
        ),
        Chunk("b#1", "b", "VPN access", "install the vpn client and sign in with mfa", "b.md"),
        Chunk("c#1", "c", "Printer queue", "clear the stuck print spooler queue", "c.md"),
    ]
