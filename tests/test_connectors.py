"""
tests/test_connectors.py — Tests des connecteurs OSV et ElectricityMaps
EcoSecOps Orchestrator — Hackathon IBM Bob 2.0

Tous les tests fonctionnent en mode offline complet (aucun vrai appel réseau).
"""

import pytest
import httpx
import respx
from unittest.mock import AsyncMock, patch

from connectors.osv_client import check_package, scan_requirements
from connectors.electricity_client import get_carbon_intensity

# ---------------------------------------------------------------------------
# Constantes de référence
# ---------------------------------------------------------------------------

OSV_URL = "https://api.osv.dev/v1/query"
ELECTRICITY_URL = "https://api.electricitymap.org/v3/carbon-intensity/latest"

OSV_JINJA2_RESPONSE = {
    "vulns": [
        {
            "id": "GHSA-fe52-489u-72pt",
            "summary": "HTML injection in Jinja2",
            "details": "Jinja2 before 2.11.3 allows HTML injection...",
            "severity": [
                {
                    "type": "CVSS_V3",
                    "score": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:N",
                }
            ],
            "affected": [
                {
                    "package": {"name": "jinja2", "ecosystem": "PyPI"},
                    "ranges": [
                        {
                            "type": "ECOSYSTEM",
                            "events": [
                                {"introduced": "0"},
                                {"fixed": "2.11.3"},
                            ],
                        }
                    ],
                }
            ],
        }
    ]
}

ELECTRICITY_LIVE_RESPONSE = {
    "zone": "US-NY",
    "carbonIntensity": 240,
    "datetime": "2026-09-25T15:00:00.000Z",
    "updatedAt": "2026-09-25T14:50:00.000Z",
    "emissionFactorType": "lifecycle",
    "isEstimated": False,
    "estimationMethod": "TIME_SLIDER",
}


# ===========================================================================
# Tests OSV — check_package()
# ===========================================================================


@pytest.mark.asyncio
async def test_check_package_mock_fallback_on_network_error():
    """Fallback mock si ConnectError vers OSV."""
    with respx.mock:
        respx.post(OSV_URL).mock(side_effect=httpx.ConnectError("offline"))

        result = await check_package("jinja2", "2.11.2")

    assert result["is_mock"] is True
    assert len(result["vulns"]) == 1
    vuln = result["vulns"][0]
    assert vuln["fixed_version"] == "2.11.3"
    assert vuln["cvss_score"] == 7.5


@pytest.mark.asyncio
async def test_check_package_success_live_response():
    """Réponse live OSV parsée correctement."""
    with respx.mock:
        respx.post(OSV_URL).mock(
            return_value=httpx.Response(200, json=OSV_JINJA2_RESPONSE)
        )

        result = await check_package("jinja2", "2.11.2")

    assert result["is_mock"] is False
    assert len(result["vulns"]) > 0
    vuln = result["vulns"][0]
    assert vuln["fixed_version"] == "2.11.3"
    assert vuln["id"] == "GHSA-fe52-489u-72pt"


@pytest.mark.asyncio
async def test_check_package_no_vulns():
    """Package propre : réponse OSV avec liste vulns vide."""
    with respx.mock:
        respx.post(OSV_URL).mock(
            return_value=httpx.Response(200, json={"vulns": []})
        )

        result = await check_package("requests", "2.31.0")

    assert result["is_mock"] is False
    assert result["vulns"] == []


@pytest.mark.asyncio
async def test_check_package_http_error_returns_mock():
    """HTTP 500 depuis OSV → fallback mock (autre package que jinja2 → vulns vide)."""
    with respx.mock:
        respx.post(OSV_URL).mock(return_value=httpx.Response(500))

        result = await check_package("somepackage", "1.0.0")

    assert result["is_mock"] is True
    assert result["vulns"] == []


@pytest.mark.asyncio
async def test_scan_requirements_parses_file(tmp_path):
    """scan_requirements ne traite que les lignes avec '=='."""
    req_file = tmp_path / "requirements.txt"
    req_file.write_text(
        "# commentaire\n"
        "jinja2==2.11.2\n"
        "requests>=2.28.0\n"
        "flask==2.0.1\n",
        encoding="utf-8",
    )

    mock_check = AsyncMock(
        side_effect=lambda name, version: {
            "name": name,
            "version": version,
            "ecosystem": "PyPI",
            "vulns": [],
            "is_mock": False,
        }
    )

    with patch("connectors.osv_client.check_package", mock_check):
        results = await scan_requirements(str(req_file))

    # Seules jinja2 et flask ont == ; requests a >= et doit être ignoré
    assert len(results) == 2
    called_names = [call.args[0] for call in mock_check.call_args_list]
    assert "jinja2" in called_names
    assert "flask" in called_names
    assert "requests" not in called_names


# ===========================================================================
# Tests ElectricityMaps — get_carbon_intensity()
# ===========================================================================


@pytest.mark.asyncio
async def test_get_carbon_intensity_no_api_key_returns_mock(monkeypatch):
    """Sans clé API → retourne le mock directement."""
    monkeypatch.setattr(
        "connectors.electricity_client.settings",
        type("S", (), {"has_electricity_maps_key": False})(),
    )

    result = await get_carbon_intensity()

    assert result == {"zone": "US-NY", "carbonIntensity": 210, "isMock": True}


@pytest.mark.asyncio
async def test_get_carbon_intensity_network_error_returns_mock(monkeypatch):
    """ConnectError réseau avec clé configurée → fallback mock."""
    monkeypatch.setattr(
        "connectors.electricity_client.settings",
        type(
            "S",
            (),
            {
                "has_electricity_maps_key": True,
                "electricity_maps_api_key": "fake-key",
            },
        )(),
    )

    with respx.mock:
        respx.get(ELECTRICITY_URL).mock(
            side_effect=httpx.ConnectError("offline")
        )
        result = await get_carbon_intensity()

    assert result == {"zone": "US-NY", "carbonIntensity": 210, "isMock": True}


@pytest.mark.asyncio
async def test_get_carbon_intensity_live_response(monkeypatch):
    """Réponse HTTP 200 → données live avec isMock=False et carbonIntensity=240."""
    monkeypatch.setattr(
        "connectors.electricity_client.settings",
        type(
            "S",
            (),
            {
                "has_electricity_maps_key": True,
                "electricity_maps_api_key": "fake-key",
            },
        )(),
    )

    with respx.mock:
        respx.get(ELECTRICITY_URL).mock(
            return_value=httpx.Response(200, json=ELECTRICITY_LIVE_RESPONSE)
        )
        result = await get_carbon_intensity()

    assert result["isMock"] is False
    assert result["carbonIntensity"] == 240
    assert result["zone"] == "US-NY"
