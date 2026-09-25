"""
tests/test_backend.py — Tests des endpoints FastAPI
EcoSecOps Orchestrator — Hackathon IBM Bob 2.0

Tous les tests fonctionnent en mode offline grâce aux mocks des connecteurs.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from backend.main import app

# ---------------------------------------------------------------------------
# Données mock réutilisables
# ---------------------------------------------------------------------------

MOCK_PACKAGES = [
    {
        "name": "jinja2",
        "version": "2.11.2",
        "ecosystem": "PyPI",
        "vulns": [
            {
                "id": "GHSA-fe52-489u-72pt",
                "summary": "HTML injection in Jinja2",
                "cvss_score": 7.5,
                "fixed_version": "2.11.3",
            }
        ],
        "is_mock": True,
    }
]

MOCK_CARBON = {"zone": "US-NY", "carbonIntensity": 210, "isMock": True}

MOCK_PATCH_RESULT = {
    "patched": [{"name": "jinja2", "old_version": "2.11.2", "new_version": "2.11.3"}],
    "unchanged": [],
    "total_patched": 1,
}

# ---------------------------------------------------------------------------
# Client de test synchrone (FastAPI TestClient)
# ---------------------------------------------------------------------------

client = TestClient(app)


# ===========================================================================
# Tests GET /health
# ===========================================================================


def test_health_returns_ok():
    """GET /health retourne {"status": "ok"} avec code 200."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ===========================================================================
# Tests POST /api/audit
# ===========================================================================


@pytest.mark.asyncio
async def test_audit_success(tmp_path):
    """POST /api/audit avec un requirements.txt valide → réponse complète."""
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("jinja2==2.11.2\n", encoding="utf-8")

    with (
        patch(
            "backend.main.scan_requirements",
            new=AsyncMock(return_value=MOCK_PACKAGES),
        ),
        patch(
            "backend.main.get_carbon_intensity",
            new=AsyncMock(return_value=MOCK_CARBON),
        ),
    ):
        with TestClient(app) as c:
            response = c.post(
                "/api/audit",
                json={
                    "requirements_path": str(req_file),
                    "zone": "US-NY",
                    "runtime_hours": 1.0,
                    "cpu_watts": 10.0,
                    "cpu_utilization": 0.5,
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert "sci" in data
    assert "carbon_intensity" in data
    assert data["carbon_intensity"] == 210
    assert data["carbon_is_mock"] is True
    assert data["total_vulnerabilities"] == 1
    assert len(data["packages"]) == 1
    pkg = data["packages"][0]
    assert pkg["name"] == "jinja2"
    assert pkg["version"] == "2.11.2"
    assert pkg["spsc"] > 0
    assert "optimizations" in data


@pytest.mark.asyncio
async def test_audit_file_not_found():
    """POST /api/audit avec fichier inexistant → HTTP 404."""
    with patch(
        "backend.main.scan_requirements",
        new=AsyncMock(side_effect=FileNotFoundError("not found")),
    ):
        with TestClient(app) as c:
            response = c.post(
                "/api/audit",
                json={"requirements_path": "/nonexistent/requirements.txt"},
            )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_audit_unexpected_error():
    """POST /api/audit erreur inattendue → HTTP 500."""
    with patch(
        "backend.main.scan_requirements",
        new=AsyncMock(side_effect=RuntimeError("boom")),
    ):
        with TestClient(app) as c:
            response = c.post("/api/audit", json={})

    assert response.status_code == 500


# ===========================================================================
# Tests POST /api/remediate
# ===========================================================================


@pytest.mark.asyncio
async def test_remediate_success(tmp_path):
    """POST /api/remediate → 1 package patché, message succès."""
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("jinja2==2.11.2\n", encoding="utf-8")

    with (
        patch(
            "backend.main.scan_requirements",
            new=AsyncMock(return_value=MOCK_PACKAGES),
        ),
        patch(
            "backend.main.patch_requirements",
            return_value=MOCK_PATCH_RESULT,
        ),
    ):
        with TestClient(app) as c:
            response = c.post(
                "/api/remediate",
                json={"requirements_path": str(req_file), "zone": "US-NY"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["total_patched"] == 1
    assert len(data["patched"]) == 1
    assert data["patched"][0]["name"] == "jinja2"
    assert "patché" in data["message"]


@pytest.mark.asyncio
async def test_remediate_no_patches(tmp_path):
    """POST /api/remediate → aucun patch disponible → message informatif."""
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("requests==2.31.0\n", encoding="utf-8")

    no_patch_result = {
        "patched": [],
        "unchanged": [{"name": "requests", "reason": "no fixed_version available"}],
        "total_patched": 0,
    }

    with (
        patch(
            "backend.main.scan_requirements",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "backend.main.patch_requirements",
            return_value=no_patch_result,
        ),
    ):
        with TestClient(app) as c:
            response = c.post(
                "/api/remediate",
                json={"requirements_path": str(req_file)},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["total_patched"] == 0
    assert "Aucun patch" in data["message"]


@pytest.mark.asyncio
async def test_remediate_file_not_found():
    """POST /api/remediate avec fichier inexistant → HTTP 404."""
    with patch(
        "backend.main.scan_requirements",
        new=AsyncMock(side_effect=FileNotFoundError("not found")),
    ):
        with TestClient(app) as c:
            response = c.post(
                "/api/remediate",
                json={"requirements_path": "/nonexistent/req.txt"},
            )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_remediate_patch_error(tmp_path):
    """Erreur dans patch_requirements → HTTP 500."""
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("jinja2==2.11.2\n", encoding="utf-8")

    with (
        patch(
            "backend.main.scan_requirements",
            new=AsyncMock(return_value=MOCK_PACKAGES),
        ),
        patch(
            "backend.main.patch_requirements",
            side_effect=RuntimeError("disk full"),
        ),
    ):
        with TestClient(app) as c:
            response = c.post(
                "/api/remediate",
                json={"requirements_path": str(req_file)},
            )

    assert response.status_code == 500
