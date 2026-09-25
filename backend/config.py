"""
backend/config.py — Gestion des Variables d'Environnement
EcoSecOps Orchestrator — Hackathon IBM Bob 2.0

Charge toutes les variables d'environnement depuis le fichier .env via python-dotenv.
Aucune valeur sensible ne doit être hardcodée dans ce fichier.
"""

import os
from dotenv import load_dotenv

# Charger les variables depuis .env (ignoré si absent, ex. en production CI)
load_dotenv()


class Settings:
    """
    Paramètres de configuration de l'application chargés depuis les variables d'environnement.

    Toutes les valeurs sensibles (clés API) sont lues exclusivement depuis l'environnement.
    Les valeurs par défaut ne contiennent aucun secret réel.
    """

    # --- ElectricityMaps API ---
    electricity_maps_api_key: str = os.getenv("ELECTRICITY_MAPS_API_KEY", "")
    """Clé d'authentification ElectricityMaps (header: auth-token). Vide = mode mock."""

    # --- OSV.dev API ---
    osv_api_url: str = os.getenv("OSV_API_URL", "https://api.osv.dev/v1/query")
    """Endpoint de l'API OSV.dev pour les requêtes de vulnérabilités."""

    # --- Application ---
    app_env: str = os.getenv("APP_ENV", "development")
    """Environnement d'exécution : development | production | test."""

    port: int = int(os.getenv("PORT", "8000"))
    """Port d'écoute du serveur FastAPI (uvicorn)."""

    # --- Frontend ---
    backend_url: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    """URL du backend FastAPI consommée par le frontend Streamlit."""

    @property
    def is_production(self) -> bool:
        """Retourne True si l'application tourne en mode production."""
        return self.app_env.lower() == "production"

    @property
    def is_test(self) -> bool:
        """Retourne True si l'application tourne en mode test."""
        return self.app_env.lower() == "test"

    @property
    def has_electricity_maps_key(self) -> bool:
        """Retourne True si une clé ElectricityMaps est configurée (mode live)."""
        return bool(self.electricity_maps_api_key)


# Instance singleton utilisée dans tout le projet
settings = Settings()
