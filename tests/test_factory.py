from __future__ import annotations

import pytest

from btp_genai_orchestration.config import AICORE_ENV_VARS, load_settings
from btp_genai_orchestration.factory import create_backend
from btp_genai_orchestration.mock_backend import MockBackend


def test_factory_returns_mock_without_credentials() -> None:
    backend = create_backend(load_settings(load_env_file=False))
    assert isinstance(backend, MockBackend)
    assert backend.name == "mock"


def test_factory_selects_live_when_credentials_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in AICORE_ENV_VARS:
        monkeypatch.setenv(name, "dummy")
    settings = load_settings(load_env_file=False)
    # The factory must take the LIVE path (never return a MockBackend). Without the
    # [live] extra installed it raises a clear RuntimeError; with the SDK installed
    # it returns a LiveBackend. Either outcome proves it did not silently fall back.
    try:
        backend = create_backend(settings)
    except RuntimeError as exc:
        assert "LIVE mode requires the SAP SDK" in str(exc)
        return
    assert backend.name == "live"
    assert not isinstance(backend, MockBackend)
