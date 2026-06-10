from __future__ import annotations

from pathlib import Path

import pytest

from btp_genai_orchestration.store import (
    build_index,
    chunk_document,
    ingest,
    load_index,
    save_index,
)


def test_chunk_document_splits_on_headings(tmp_path: Path) -> None:
    doc = tmp_path / "sample.md"
    doc.write_text(
        "# Title\n\nintro text\n\n## Section A\n\nbody a\n\n## Section B\n\nbody b\n",
        encoding="utf-8",
    )
    chunks = chunk_document(doc)
    titles = [c.title for c in chunks]
    assert titles == ["Title", "Section A", "Section B"]
    assert all(c.doc_id == "sample" for c in chunks)
    assert chunks[0].chunk_id == "sample#1"
    assert "intro text" in chunks[0].text


def test_chunk_document_keeps_preheading_content(tmp_path: Path) -> None:
    doc = tmp_path / "x.md"
    doc.write_text("loose text before any heading\n\n## Real\n\nmore\n", encoding="utf-8")
    chunks = chunk_document(doc)
    assert chunks[0].title == "Overview"
    assert "loose text" in chunks[0].text


def test_build_index_reads_real_runbooks() -> None:
    docs = Path(__file__).resolve().parents[1] / "data" / "runbooks"
    chunks = build_index(docs)
    assert len(chunks) >= 5
    assert any(c.doc_id == "tablet-reset" for c in chunks)


def test_build_index_empty_dir_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        build_index(tmp_path)


def test_build_index_missing_dir_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        build_index(tmp_path / "nope")


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    docs = Path(__file__).resolve().parents[1] / "data" / "runbooks"
    index = tmp_path / "nested" / "index.json"
    original = ingest(docs, index)
    assert index.is_file()
    reloaded = load_index(index)
    assert [c.chunk_id for c in reloaded] == [c.chunk_id for c in original]
    assert reloaded[0].text == original[0].text


def test_load_index_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_index(tmp_path / "absent.json")


def test_save_index_creates_parents(tmp_path: Path) -> None:
    from btp_genai_orchestration.models import Chunk

    target = tmp_path / "a" / "b" / "c.json"
    save_index([Chunk("d#1", "d", "T", "text", "d.md")], target)
    assert target.is_file()
