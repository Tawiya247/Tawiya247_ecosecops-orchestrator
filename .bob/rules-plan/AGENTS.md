# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Architectural Constraints (Non-Obvious)

- **Dependency direction is strict**: `frontend` → `backend` → `core` + `connectors`. `core` and `connectors` are peers with no cross-dependency.
- **`settings` is evaluated at import time** (plain class, not Pydantic BaseSettings) — architectural consequence: connectors cannot be tested with different API keys without monkeypatching `settings` attributes directly.
- **Mock fallback is architectural, not optional**: the system is designed to run in a fully air-gapped environment (hackathon judging). Any refactor that removes the mock path breaks the demo.
- **Tâches 3 and 4 are parallelizable** (`metrics.py` and `remediator.py` have zero coupling) — plan accordingly when scoping work.
- **No Pydantic v1/v2 mixing**: FastAPI ≥0.111 requires Pydantic v2. Do not introduce v1-style validators (`@validator`) — use `@field_validator`.
- The `frontend/app.py` calls the backend via HTTP (not direct import) — the backend must be running separately when the frontend is used.
- `remediator.patch_requirements()` mutates `requirements.txt` on disk — the audit endpoint must be called before remediate (state dependency between endpoints).
