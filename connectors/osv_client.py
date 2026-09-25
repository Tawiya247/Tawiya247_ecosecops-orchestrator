"""
connectors/osv_client.py — Client OSV.dev
EcoSecOps Orchestrator — Hackathon IBM Bob 2.0

Interroge l'API OSV.dev pour détecter les vulnérabilités connues d'un package
Python (ou autre écosystème). Fournit un fallback mock en cas d'échec réseau.
"""

import httpx

from backend.config import settings

# Import optionnel de la lib `cvss` (non listée dans requirements.txt)
try:
    from cvss import CVSS3 as _CVSS3
    _CVSS_AVAILABLE = True
except ImportError:
    _CVSS_AVAILABLE = False


# ---------------------------------------------------------------------------
# Helpers privés
# ---------------------------------------------------------------------------

def _extract_cvss_score(severity: list) -> float:
    """Extrait le score CVSS numérique depuis la liste ``severity`` d'une vuln OSV.

    Args:
        severity: Liste de dicts ``{"type": ..., "score": ...}`` issus de la
            réponse OSV.dev.

    Returns:
        Score CVSS (float) si trouvé et parseable, sinon ``0.0``.
    """
    for entry in severity:
        if entry.get("type") == "CVSS_V3":
            vector = entry.get("score", "")
            if _CVSS_AVAILABLE and vector:
                try:
                    return float(_CVSS3(vector).base_score)
                except Exception:
                    return 0.0
            return 0.0
    return 0.0


def _extract_fixed_version(affected: list) -> str:
    """Extrait la première version corrective depuis la liste ``affected`` OSV.

    Parcourt les ranges de type ``ECOSYSTEM`` et renvoie la valeur du premier
    événement ``fixed`` trouvé.

    Args:
        affected: Liste ``affected[]`` d'une vulnérabilité OSV.dev.

    Returns:
        Chaîne de version corrective, ou ``""`` si introuvable.
    """
    for pkg in affected:
        for rng in pkg.get("ranges", []):
            if rng.get("type") == "ECOSYSTEM":
                for event in rng.get("events", []):
                    if "fixed" in event:
                        return event["fixed"]
    return ""


def _parse_vuln(vuln: dict) -> dict:
    """Normalise une vulnérabilité brute OSV en dict interne.

    Args:
        vuln: Objet vulnérabilité tel que retourné par l'API OSV.dev.

    Returns:
        Dict avec les clés ``id``, ``summary``, ``cvss_score``, ``fixed_version``.
    """
    return {
        "id": vuln.get("id", ""),
        "summary": vuln.get("summary", ""),
        "cvss_score": _extract_cvss_score(vuln.get("severity", [])),
        "fixed_version": _extract_fixed_version(vuln.get("affected", [])),
    }


def _mock_result(name: str, version: str, ecosystem: str) -> dict:
    """Construit un résultat mock de fallback.

    Retourne une vulnérabilité simulée jinja2==2.11.2 si le package demandé
    est ``jinja2``, sinon retourne une liste de vulnérabilités vide.

    Args:
        name: Nom du package.
        version: Version du package.
        ecosystem: Écosystème du package (ex. ``"PyPI"``).

    Returns:
        Dict résultat avec ``is_mock=True``.
    """
    if name.lower() == "jinja2":
        vulns = [
            {
                "id": "GHSA-fe52-489u-72pt",
                "summary": "HTML injection in Jinja2",
                "cvss_score": 7.5,
                "fixed_version": "2.11.3",
            }
        ]
    else:
        vulns = []

    return {
        "name": name,
        "version": version,
        "ecosystem": ecosystem,
        "vulns": vulns,
        "is_mock": True,
    }


# ---------------------------------------------------------------------------
# API publique
# ---------------------------------------------------------------------------

async def check_package(
    name: str,
    version: str,
    ecosystem: str = "PyPI",
) -> dict:
    """Interroge l'API OSV.dev pour les vulnérabilités d'un package donné.

    Args:
        name: Nom du package (ex. ``"jinja2"``).
        version: Version du package (ex. ``"2.11.2"``).
        ecosystem: Écosystème du gestionnaire de paquets (défaut ``"PyPI"``).

    Returns:
        Dict avec les clés :
        - ``name`` (str)
        - ``version`` (str)
        - ``ecosystem`` (str)
        - ``vulns`` (list[dict]) — chaque vuln contient ``id``, ``summary``,
          ``cvss_score`` (float), ``fixed_version`` (str)
        - ``is_mock`` (bool) — ``True`` si la réponse provient du fallback mock
    """
    payload = {
        "package": {"name": name, "ecosystem": ecosystem},
        "version": version,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(settings.osv_api_url, json=payload)
            response.raise_for_status()
            data = response.json()

        vulns = [_parse_vuln(v) for v in data.get("vulns", [])]
        return {
            "name": name,
            "version": version,
            "ecosystem": ecosystem,
            "vulns": vulns,
            "is_mock": False,
        }
    except Exception:
        return _mock_result(name, version, ecosystem)


async def scan_requirements(path: str = "requirements.txt") -> list[dict]:
    """Analyse un fichier ``requirements.txt`` et vérifie chaque dépendance.

    Lit le fichier ligne par ligne, ignore les commentaires et les lignes vides,
    et appelle :func:`check_package` pour chaque entrée au format ``package==version``.

    Args:
        path: Chemin vers le fichier requirements (défaut ``"requirements.txt"``).

    Returns:
        Liste de dicts résultats tels que retournés par :func:`check_package`.
    """
    results: list[dict] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "==" not in line:
                continue
            name, _, version = line.partition("==")
            # Ne conserver que la partie version (ignorer les extras éventuels)
            version = version.split(";")[0].strip()
            name = name.strip()
            result = await check_package(name, version)
            results.append(result)
    return results
