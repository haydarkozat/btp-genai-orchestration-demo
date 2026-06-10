from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("fastapi", reason="API extra not installed")

from fastapi.testclient import TestClient

from btp_genai_orchestration import api
from btp_genai_orchestration.store import ingest


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    docs = Path(__file__).resolve().parents[1] / "data" / "runbooks"
    index = tmp_path / "index.json"
    monkeypatch.setenv("RAG_DOCS_DIR", str(docs))
    monkeypatch.setenv("RAG_INDEX_PATH", str(index))
    ingest(docs, index)
    api._pipeline.cache_clear()  # the pipeline is cached per process
    return TestClient(api.app)


def test_health_reports_mock(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "backend": "mock"}


def test_ask_returns_answer_with_citations(client: TestClient) -> None:
    resp = client.post("/ask", json={"question": "How do I reset a student tablet?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["backend"] == "mock"
    assert body["citations"]
    assert any("tablet-reset" in c["chunk_id"] for c in body["citations"])
