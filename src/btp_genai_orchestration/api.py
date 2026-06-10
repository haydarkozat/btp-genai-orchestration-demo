"""Optional thin FastAPI wrapper exposing POST /ask.

Deliberately minimal — the real logic lives in the pipeline. Install with the
``[api]`` extra and run: ``uvicorn btp_genai_orchestration.api:app``.
"""

from __future__ import annotations

from dataclasses import asdict
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .config import load_settings
from .pipeline import RagPipeline, index_exists

app = FastAPI(title="BTP GenAI Hub Orchestration RAG", version="0.1.0")


class AskRequest(BaseModel):
    question: str


class CitationModel(BaseModel):
    chunk_id: str
    title: str
    source_path: str
    score: float


class AskResponse(BaseModel):
    question: str
    answer: str
    backend: str
    model: str | None
    citations: list[CitationModel]


@lru_cache(maxsize=1)
def _pipeline() -> RagPipeline:
    return RagPipeline.from_settings(load_settings())


@app.get("/health")
def health() -> dict[str, object]:
    settings = load_settings()
    return {"status": "ok", "backend": "live" if settings.use_live else "mock"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    if not index_exists():
        raise HTTPException(status_code=503, detail="No index. Run `demo ingest` first.")
    answer = _pipeline().ask(request.question)
    return AskResponse(
        question=answer.question,
        answer=answer.text,
        backend=answer.backend,
        model=answer.model,
        citations=[CitationModel(**asdict(c)) for c in answer.citations],
    )
