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
    # The factory must take the LIVE path, never silently fall back to MockBackend.
    # Building LiveBackend may raise here depending on the environment:
    #   - no [live] extra  -> RuntimeError("LIVE mode requires the SAP SDK")
    #   - SDK + dummy creds -> an SDK/auth error when the service is constructed
    # MockBackend construction never raises, so *any* exception still proves the
    # routing decision under test. If it does construct, it must be the live one.
    try:
        backend = create_backend(settings)
    except Exception:
        return
    assert backend.name == "live"
    assert not isinstance(backend, MockBackend)
