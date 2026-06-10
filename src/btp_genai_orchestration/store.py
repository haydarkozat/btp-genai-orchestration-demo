"""Document ingestion and the on-disk chunk index.

`ingest` parses each Markdown runbook into section-level chunks (split on ``##``
headings) and persists them as JSON. `ask` loads that JSON back. Deliberately a
plain file — a HANA Cloud vector table is the production equivalent (see README).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .models import Chunk

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def _split_sections(text: str) -> list[tuple[str, str]]:
    """Split Markdown into ``(title, body)`` sections on the first two heading levels.

    Content before the first heading is attached to an ``Overview`` section so no
    text is silently dropped.
    """
    sections: list[tuple[str, list[str]]] = []
    current_title = "Overview"
    current_body: list[str] = []

    for line in text.splitlines():
        match = _HEADING_RE.match(line)
        if match and len(match.group(1)) <= 2:
            if current_body:
                sections.append((current_title, current_body))
            current_title = match.group(2).strip()
            current_body = []
        else:
            current_body.append(line)

    if current_body:
        sections.append((current_title, current_body))

    out: list[tuple[str, str]] = []
    for title, body in sections:
        joined = "\n".join(body).strip()
        if joined:
            out.append((title, joined))
    return out


def chunk_document(path: Path) -> list[Chunk]:
    """Parse a single Markdown file into chunks."""
    doc_id = path.stem
    text = path.read_text(encoding="utf-8")
    chunks: list[Chunk] = []
    for index, (title, body) in enumerate(_split_sections(text), start=1):
        chunks.append(
            Chunk(
                chunk_id=f"{doc_id}#{index}",
                doc_id=doc_id,
                title=title,
                text=body,
                source_path=str(path),
            )
        )
    return chunks


def build_index(docs_dir: Path) -> list[Chunk]:
    """Chunk every ``*.md`` file in ``docs_dir`` (sorted for determinism)."""
    if not docs_dir.is_dir():
        raise FileNotFoundError(f"Docs directory not found: {docs_dir}")
    chunks: list[Chunk] = []
    for path in sorted(docs_dir.glob("*.md")):
        chunks.extend(chunk_document(path))
    if not chunks:
        raise ValueError(f"No Markdown documents found in {docs_dir}")
    return chunks


def save_index(chunks: list[Chunk], index_path: Path) -> None:
    """Persist chunks as JSON, creating parent directories as needed."""
    index_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "chunks": [
            {
                "chunk_id": c.chunk_id,
                "doc_id": c.doc_id,
                "title": c.title,
                "text": c.text,
                "source_path": c.source_path,
            }
            for c in chunks
        ],
    }
    index_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def load_index(index_path: Path) -> list[Chunk]:
    """Load chunks previously written by :func:`save_index`."""
    if not index_path.is_file():
        raise FileNotFoundError(f"Index not found at {index_path}. Run `demo ingest` first.")
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    return [
        Chunk(
            chunk_id=item["chunk_id"],
            doc_id=item["doc_id"],
            title=item["title"],
            text=item["text"],
            source_path=item["source_path"],
        )
        for item in payload["chunks"]
    ]


def ingest(docs_dir: Path, index_path: Path) -> list[Chunk]:
    """Convenience: build the index from ``docs_dir`` and persist it."""
    chunks = build_index(docs_dir)
    save_index(chunks, index_path)
    return chunks
