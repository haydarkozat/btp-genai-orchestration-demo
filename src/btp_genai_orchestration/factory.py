"""Backend selection — the *only* place the MOCK/LIVE decision is made."""

from __future__ import annotations

from .backend import LLMBackend
from .config import Settings
from .mock_backend import MockBackend


def create_backend(settings: Settings) -> LLMBackend:
    """Return the backend dictated by ``settings`` — MockBackend or LiveBackend.

    The LiveBackend (and therefore the SAP SDK) is imported lazily so that nothing
    in the MOCK path depends on the ``[live]`` extra being installed.
    """
    if settings.use_live:
        from .live_backend import LiveBackend

        return LiveBackend(settings)
    return MockBackend()
