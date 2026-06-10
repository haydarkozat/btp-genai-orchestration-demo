"""Configuration and backend-mode resolution.

All environment access is funnelled through :func:`load_settings` so the rest of
the codebase never reads ``os.environ`` directly. The mode-selection logic lives
here (and only here): every other module just asks the factory for *a* backend.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from dotenv import load_dotenv

# Exact env var names the SAP `gen_ai_hub` SDK reads to authenticate against
# AI Core. Confirmed against the SDK / SAP Help documentation — do not rename.
AICORE_ENV_VARS = (
    "AICORE_AUTH_URL",
    "AICORE_CLIENT_ID",
    "AICORE_CLIENT_SECRET",
    "AICORE_BASE_URL",
)


class BackendMode(StrEnum):
    AUTO = "auto"
    MOCK = "mock"
    LIVE = "live"


@dataclass(frozen=True, slots=True)
class Settings:
    """Resolved runtime configuration."""

    mode: BackendMode
    model: str
    deployment_url: str | None
    resource_group: str
    top_k: int
    index_path: Path
    docs_dir: Path
    credentials_present: bool

    @property
    def use_live(self) -> bool:
        """Whether the LIVE backend should be used.

        LIVE only when explicitly requested or when AUTO detects credentials.
        Anything else falls back to MOCK — the safe, offline default.
        """
        if self.mode is BackendMode.LIVE:
            return True
        if self.mode is BackendMode.MOCK:
            return False
        return self.credentials_present


def _credentials_present() -> bool:
    return all(os.environ.get(name) for name in AICORE_ENV_VARS)


def load_settings(*, load_env_file: bool = True) -> Settings:
    """Build :class:`Settings` from environment variables (and an optional .env)."""
    if load_env_file:
        # Does nothing if there is no .env file; never overrides real env vars.
        load_dotenv(override=False)

    mode = BackendMode(os.environ.get("BACKEND_MODE", "auto").strip().lower())
    top_k_raw = os.environ.get("RAG_TOP_K", "3").strip()
    try:
        top_k = max(1, int(top_k_raw))
    except ValueError:
        top_k = 3

    return Settings(
        mode=mode,
        model=os.environ.get("ORCHESTRATION_MODEL", "gpt-4o-mini").strip(),
        deployment_url=(os.environ.get("AICORE_ORCHESTRATION_DEPLOYMENT_URL") or None),
        resource_group=os.environ.get("AICORE_RESOURCE_GROUP", "default").strip(),
        top_k=top_k,
        index_path=Path(os.environ.get("RAG_INDEX_PATH", ".btp_rag/index.json")),
        docs_dir=Path(os.environ.get("RAG_DOCS_DIR", "data/runbooks")),
        credentials_present=_credentials_present(),
    )
