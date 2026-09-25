"""
connectors/electricity_client.py — Client ElectricityMaps
EcoSecOps Orchestrator — Hackathon IBM Bob 2.0

Fournit un client async pour l'API ElectricityMaps (carbon-intensity/latest).
Retourne un mock si la clé API est absente ou en cas d'erreur réseau/HTTP.
"""

import httpx

from backend.config import settings

_ENDPOINT = "https://api.electricitymap.org/v3/carbon-intensity/latest"
_MOCK_CARBON_INTENSITY = 210
_TIMEOUT_SECONDS = 10


def _mock(zone: str) -> dict:
    """Retourne la réponse mock de secours.

    Args:
        zone: Code de zone ElectricityMaps (ex. ``"US-NY"``).

    Returns:
        Dict avec ``carbonIntensity``, ``zone`` et ``isMock: True``.
    """
    return {"zone": zone, "carbonIntensity": _MOCK_CARBON_INTENSITY, "isMock": True}


async def get_carbon_intensity(zone: str = "US-NY") -> dict:
    """Récupère l'intensité carbone en temps réel pour une zone donnée.

    Interroge l'API ElectricityMaps si une clé est configurée, sinon retourne
    immédiatement le mock. En cas d'exception réseau ou HTTP, retourne également
    le mock de secours.

    Args:
        zone: Code de zone ElectricityMaps (ex. ``"US-NY"``). Par défaut ``"US-NY"``.

    Returns:
        Dict contenant au minimum les champs ``zone``, ``carbonIntensity`` et
        ``isMock``. En mode live, tous les champs renvoyés par l'API sont présents
        avec ``isMock: False``.
    """
    if not settings.has_electricity_maps_key:
        return _mock(zone)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.get(
                _ENDPOINT,
                params={"zone": zone},
                headers={"auth-token": settings.electricity_maps_api_key},
            )
            response.raise_for_status()
            data: dict = response.json()
            data["isMock"] = False
            return data
    except Exception:
        return _mock(zone)
