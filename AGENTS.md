# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project

**EcoSecOps Orchestrator** — Python 3.11+, FastAPI backend, Streamlit frontend, async httpx connectors.
Hackathon IBM Bob 2.0 project. See `ecosecops-plan.md` for the task roadmap.

## Commands

```bash
# Backend
uvicorn backend.main:app --reload --port 8000

# Frontend
streamlit run frontend/app.py

# Tests (all)
pytest --cov=. --cov-report=term-missing

# Single test
pytest tests/test_metrics.py::test_calculate_sci -v

# Single file
pytest tests/test_connectors.py -v
```

> Coverage target: **>80%**. Run `pytest --cov` before marking any task done.

## Critical Architecture Rules

- **`connectors/` must never import from `backend/`** — one-way dependency enforced by design.
- **No circular imports** between `connectors/`, `core/`, `backend/`.
- All API keys are read exclusively from `backend/config.py` → `settings` singleton (never hardcode, never `os.getenv()` directly in connectors or core).
- **Every HTTP client must have a mock fallback** — the system must work fully offline (no real API calls in tests).

## Mock Fallback Contracts (non-negotiable)

- `connectors/osv_client.py` fallback: `jinja2==2.11.2`, CVSS=7.5, fixed=`2.11.3`
- `connectors/electricity_client.py` fallback: `{"zone": "US-NY", "carbonIntensity": 210, "isMock": true}`
- Trigger condition: missing API key OR any network exception.

## Math Formulas (implement exactly)

```
SCI = ((E × I) + M) / R          # ISO/IEC 21031:2024; guard R != 0
SPSC = 0.5·CVSS + 0.3·(I_act/I_ref) + 0.2·U_CPU   # I_ref default=300
```

Default constants: `M=0.05` gCO₂e, `I_ref=300` gCO₂e/kWh, `α=0.5`, `β=0.3`, `γ=0.2`.

## Code Style

- **Type hints** on every public function — no exceptions.
- **Docstrings** on every function: Google or NumPy format. Math functions must cite ISO/IEC 21031:2024.
- Use `respx` (not `unittest.mock`) to mock `httpx` calls in tests — ensures async compatibility.
- `pytest-asyncio` is required for all async test functions (`@pytest.mark.asyncio`).

## Security (IBM monitors the public GitHub repo)

- `.env` is in both `.gitignore` AND `.bobignore` — never create a real `.env` file at repo root.
- Use `.env.example` as the only committed reference for env variables.
- `bob_sessions/*.png` excluded from Bob indexing (binary captures).

## Testing HTTP Clients

Use `respx.mock` to intercept `httpx.AsyncClient` calls. Tests must pass with zero network access.
The `APP_ENV=test` value is available via `settings.is_test` to conditionally skip live calls.
