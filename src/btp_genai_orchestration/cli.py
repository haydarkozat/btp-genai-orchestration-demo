"""Typer CLI: ``demo ingest`` and ``demo ask "..."``."""

from __future__ import annotations

from typing import Annotated

import typer

from . import __version__
from .config import load_settings
from .pipeline import RagPipeline, index_exists, run_ingest

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="RAG/grounding demo on SAP BTP Generative AI Hub orchestration.",
)


@app.command()
def ingest() -> None:
    """Chunk the sample runbooks and build the search index."""
    settings = load_settings()
    try:
        chunks = run_ingest(settings)
    except (FileNotFoundError, ValueError) as exc:
        typer.secho(f"Ingest failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    typer.secho(
        f"Ingested {len(chunks)} chunks from {settings.docs_dir} -> {settings.index_path}",
        fg=typer.colors.GREEN,
    )


@app.command()
def ask(
    question: Annotated[str, typer.Argument(help="The question to answer.")],
) -> None:
    """Answer a question, grounded in the ingested runbooks, with citations."""
    settings = load_settings()
    if not index_exists(settings):
        typer.secho("No index found. Run `demo ingest` first.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    mode = "LIVE (GenAI Hub orchestration)" if settings.use_live else "MOCK (offline stub)"
    typer.secho(f"[{mode}]", fg=typer.colors.CYAN, err=True)

    try:
        pipeline = RagPipeline.from_settings(settings)
        answer = pipeline.ask(question)
    except RuntimeError as exc:  # e.g. LIVE requested but SDK/creds unavailable
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(answer.render())


@app.command()
def info() -> None:
    """Show the resolved configuration and which backend would be used."""
    settings = load_settings()
    typer.echo(f"version:            {__version__}")
    typer.echo(f"backend mode:       {settings.mode.value}")
    typer.echo(f"resolved backend:   {'live' if settings.use_live else 'mock'}")
    typer.echo(f"credentials found:  {settings.credentials_present}")
    typer.echo(f"model (live):       {settings.model}")
    typer.echo(f"docs dir:           {settings.docs_dir}")
    typer.echo(f"index path:         {settings.index_path}")
    typer.echo(f"top_k:              {settings.top_k}")


def main() -> None:
    """Console-script entry point."""
    app()


if __name__ == "__main__":
    main()
