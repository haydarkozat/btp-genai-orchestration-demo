# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-10

### Added

- Orchestration RAG pipeline: `demo ingest` (chunk Markdown runbooks into a JSON index)
  and `demo ask "..."` (retrieve → ground → generate → cite).
- Dual-mode backend behind a single `LLMBackend` protocol:
  - **MOCK** (default): offline BM25 keyword retrieval + deterministic extractive
    generation, zero credentials, zero network.
  - **LIVE**: SAP Generative AI Hub orchestration service via `sap-ai-sdk-gen`
    (prompt template + grounding/context injection + model config); OAuth handled by
    the SDK from `AICORE_*` environment variables.
- Five realistic IT-operations runbooks as sample grounding data.
- Optional thin FastAPI wrapper (`POST /ask`, `GET /health`) under the `[api]` extra.
- Test suite (pytest) green in MOCK mode with ≥80% coverage on core logic, plus a
  `@pytest.mark.live` group skipped without credentials.
- SDK-contract test (`tests/test_live_contract.py`) that builds the LIVE backend's
  orchestration request object against the installed `sap-ai-sdk-gen` — no network,
  no credentials — so SDK API drift is caught in CI. Verified against 6.10.0.
- GitHub Actions CI: ruff lint + format check, strict mypy, pytest (MOCK) on Python
  3.11 and 3.12, plus a `sdk-contract` job that installs the `[live]` extra and runs
  the contract test.
- README with architecture diagram, SOUVERÄN-KI ↔ BTP/GenAI Hub mapping table, and an
  honest scope note; MIT license; `.env.example`; pinned `uv.lock`.

### Notes

- The brief named the now-deprecated `generative-ai-hub-sdk`; this project pins its
  maintained successor `sap-ai-sdk-gen` (same `gen_ai_hub` import namespace).

[0.1.0]: https://github.com/haydarkozat/btp-genai-orchestration-demo/releases/tag/v0.1.0
