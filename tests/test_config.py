from __future__ import annotations

import pytest

from btp_genai_orchestration.config import AICORE_ENV_VARS, BackendMode, load_settings


def _set_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in AICORE_ENV_VARS:
        monkeypatch.setenv(name, "dummy")


def test_defaults_to_mock_without_credentials() -> None:
    settings = load_settings(load_env_file=False)
    assert settings.use_live is False
    assert settings.credentials_present is False
    assert settings.mode is BackendMode.AUTO


def test_auto_switches_to_live_when_credentials_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_credentials(monkeypatch)
    settings = load_settings(load_env_file=False)
    assert settings.credentials_present is True
    assert settings.use_live is True


def test_mode_mock_forces_mock_even_with_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_credentials(monkeypatch)
    monkeypatch.setenv("BACKEND_MODE", "mock")
    assert load_settings(load_env_file=False).use_live is False


def test_mode_live_forces_live_without_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BACKEND_MODE", "live")
    assert load_settings(load_env_file=False).use_live is True


def test_invalid_top_k_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAG_TOP_K", "not-a-number")
    assert load_settings(load_env_file=False).top_k == 3


def test_top_k_minimum_is_one(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAG_TOP_K", "0")
    assert load_settings(load_env_file=False).top_k == 1
