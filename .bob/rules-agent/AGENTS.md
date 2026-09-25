# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Coding Rules (Non-Obvious)

- **Import `settings` from `backend.config`**, not `os.getenv()` directly — connectors and core must never call `os.getenv()` themselves.
- **`respx`** is the HTTP mock library (not `responses`, not `httpretty`) — use `respx.mock` decorator for async httpx tests.
- `pytest-asyncio` mode: add `@pytest.mark.asyncio` to every async test function — no auto-detection configured.
- `patch_requirements()` in `core/remediator.py` writes back to disk — tests must use a temp file, not the real `requirements.txt`.
- FastAPI endpoint descriptions live in **Pydantic model `Field(description=...)`**, not in route docstrings — this feeds Swagger.
- `settings.has_electricity_maps_key` is the canonical check before making a live ElectricityMaps call.
- `calculate_sci()` must raise or return a meaningful error when `R=0` — do not silently return 0.
- The `settings` object is a **plain class instance**, not a Pydantic `BaseSettings` — `os.getenv()` is called at class definition time, so changes to env vars after import are not reflected without reimport.

## Forbidden Patterns

- No hardcoded API keys or URLs anywhere except `backend/config.py` defaults.
- No imports from `backend/` inside `connectors/` or `core/`.
- No real network calls inside `tests/` — always mock with `respx`.
