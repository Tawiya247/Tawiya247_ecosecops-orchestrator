"""
backend/main.py — Application FastAPI
EcoSecOps Orchestrator — Hackathon IBM Bob 2.0

Expose trois endpoints :
  GET  /health           — Liveness check
  POST /api/audit        — Audit de sécurité + calcul SCI/SPSC
  POST /api/remediate    — Application des patches de sécurité

Démarrage : uvicorn backend.main:app --reload --port 8000
Documentation Swagger : http://localhost:8000/docs
"""

import asyncio

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from backend.config import settings
from connectors.osv_client import scan_requirements
from connectors.electricity_client import get_carbon_intensity
from core.metrics import calculate_sci, calculate_spsc
from core.remediator import patch_requirements, suggest_optimizations

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="EcoSecOps Orchestrator",
    version="1.0.0",
    description=(
        "Plateforme de gouvernance DevSecOps + GreenOps. "
        "Audite les dépendances open-source (OSV.dev), mesure l'empreinte carbone "
        "(SCI — ISO/IEC 21031:2024) et remédie automatiquement aux vulnérabilités."
    ),
)

# ---------------------------------------------------------------------------
# Modèles Pydantic — Requêtes
# ---------------------------------------------------------------------------


class AuditRequest(BaseModel):
    """Paramètres de la requête d'audit."""

    requirements_path: str = Field(
        default="requirements.txt",
        description="Chemin vers le fichier requirements.txt à auditer.",
    )
    zone: str = Field(
        default="US-NY",
        description="Zone ElectricityMaps pour l'intensité carbone (ex. 'US-NY', 'FR').",
    )
    runtime_hours: float = Field(
        default=1.0,
        gt=0,
        description="Durée d'exécution estimée en heures (pour le calcul SCI).",
    )
    cpu_watts: float = Field(
        default=10.0,
        gt=0,
        description="Consommation CPU en watts (pour le calcul de l'énergie E).",
    )
    cpu_utilization: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Utilisation CPU normalisée entre 0.0 et 1.0 (pour le score SPSC).",
    )


class RemediateRequest(BaseModel):
    """Paramètres de la requête de remédiation."""

    requirements_path: str = Field(
        default="requirements.txt",
        description="Chemin vers le fichier requirements.txt à patcher.",
    )
    zone: str = Field(
        default="US-NY",
        description="Zone ElectricityMaps (utilisée pour recalculer le SCI post-patch).",
    )


# ---------------------------------------------------------------------------
# Modèles Pydantic — Réponses
# ---------------------------------------------------------------------------


class VulnDetail(BaseModel):
    """Détail d'une vulnérabilité détectée."""

    id: str = Field(description="Identifiant OSV (ex. GHSA-...).")
    summary: str = Field(description="Résumé de la vulnérabilité.")
    cvss_score: float = Field(description="Score CVSS (0.0–10.0).")
    fixed_version: str = Field(description="Version corrigée recommandée.")


class PackageAudit(BaseModel):
    """Résultat d'audit pour un package."""

    name: str
    version: str
    ecosystem: str
    is_mock: bool = Field(description="True si les données proviennent du fallback mock.")
    vulns: list[VulnDetail]
    spsc: float = Field(description="Security-Carbon Priority Score pour ce package.")


class AuditResponse(BaseModel):
    """Réponse complète de l'endpoint /api/audit."""

    sci: float = Field(description="Software Carbon Intensity (gCO₂e/unité fonctionnelle).")
    carbon_intensity: float = Field(description="Intensité carbone du réseau en gCO₂e/kWh.")
    carbon_is_mock: bool = Field(description="True si l'intensité carbone est une valeur mock.")
    zone: str
    packages: list[PackageAudit]
    optimizations: list[str] = Field(description="Recommandations de réduction carbone.")
    total_vulnerabilities: int


class PatchRecord(BaseModel):
    """Enregistrement d'un patch appliqué."""

    name: str
    old_version: str
    new_version: str


class UnchangedRecord(BaseModel):
    """Enregistrement d'un package non patché."""

    name: str
    reason: str


class RemediateResponse(BaseModel):
    """Réponse complète de l'endpoint /api/remediate."""

    patched: list[PatchRecord]
    unchanged: list[UnchangedRecord]
    total_patched: int
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health", summary="Liveness check")
async def health() -> dict:
    """Vérifie que le service est opérationnel.

    Returns:
        Dict ``{"status": "ok"}`` si le service répond.
    """
    return {"status": "ok"}


@app.post("/api/audit", response_model=AuditResponse, summary="Audit de sécurité et carbone")
async def audit(request: AuditRequest) -> AuditResponse:
    """Audite un fichier requirements.txt et calcule SCI + SPSC pour chaque dépendance.

    Orchestre en parallèle :
    - `osv_client.scan_requirements()` → liste des vulnérabilités par package
    - `electricity_client.get_carbon_intensity()` → intensité carbone live

    Puis calcule pour chaque package vulnérable :
    - Score SPSC = priorité de remédiation hybride (sécurité + carbone + CPU)

    Et globalement :
    - Score SCI (ISO/IEC 21031:2024) pour l'ensemble du run

    Args:
        request: AuditRequest avec le chemin requirements.txt, la zone et les paramètres CPU.

    Returns:
        AuditResponse avec SCI, intensité carbone, liste des packages avec leurs vulns et SPSC.

    Raises:
        HTTPException 404: Si le fichier requirements.txt est introuvable.
        HTTPException 500: En cas d'erreur inattendue.
    """
    try:
        # Lancement parallèle des deux I/O
        packages_result, carbon_result = await asyncio.gather(
            scan_requirements(request.requirements_path),
            get_carbon_intensity(request.zone),
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'audit : {exc}")

    carbon_intensity: float = carbon_result.get("carbonIntensity", 210.0)
    carbon_is_mock: bool = carbon_result.get("isMock", True)

    # Calcul SCI global : E = runtime_hours × cpu_watts / 1000
    energy_kwh = (request.runtime_hours * request.cpu_watts) / 1000.0
    sci = calculate_sci(
        energy_kwh=energy_kwh,
        carbon_intensity=carbon_intensity,
    )

    # Construction des résultats par package
    package_audits: list[PackageAudit] = []
    total_vulns = 0

    for pkg in packages_result:
        vulns_raw = pkg.get("vulns", [])
        total_vulns += len(vulns_raw)

        # SPSC : on prend le CVSS max du package (worst-case)
        max_cvss = max((v.get("cvss_score", 0.0) for v in vulns_raw), default=0.0)
        spsc = calculate_spsc(
            cvss=max_cvss,
            current_intensity=carbon_intensity,
            cpu_utilization=request.cpu_utilization,
        )

        package_audits.append(
            PackageAudit(
                name=pkg["name"],
                version=pkg["version"],
                ecosystem=pkg.get("ecosystem", "PyPI"),
                is_mock=pkg.get("is_mock", False),
                vulns=[VulnDetail(**v) for v in vulns_raw],
                spsc=round(spsc, 4),
            )
        )

    # Trier par SPSC décroissant (priorité haute en premier)
    package_audits.sort(key=lambda p: p.spsc, reverse=True)

    optimizations = suggest_optimizations(sci)

    return AuditResponse(
        sci=round(sci, 6),
        carbon_intensity=carbon_intensity,
        carbon_is_mock=carbon_is_mock,
        zone=carbon_result.get("zone", request.zone),
        packages=package_audits,
        optimizations=optimizations,
        total_vulnerabilities=total_vulns,
    )


@app.post("/api/remediate", response_model=RemediateResponse, summary="Remédiation automatique")
async def remediate(request: RemediateRequest) -> RemediateResponse:
    """Applique les patches de sécurité sur requirements.txt.

    Effectue d'abord un audit pour obtenir les vulnérabilités, puis appelle
    `patch_requirements()` pour mettre à jour les versions vulnérables vers
    les versions correctives recommandées par OSV.

    Args:
        request: RemediateRequest avec le chemin requirements.txt et la zone.

    Returns:
        RemediateResponse avec les packages patchés, non patchés et un message de synthèse.

    Raises:
        HTTPException 404: Si le fichier requirements.txt est introuvable.
        HTTPException 500: En cas d'erreur inattendue lors du patch.
    """
    try:
        # Audit préalable pour obtenir les vulnérabilités
        vulnerabilities = await scan_requirements(request.requirements_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur lors du scan : {exc}")

    try:
        result = patch_requirements(request.requirements_path, vulnerabilities)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur lors du patch : {exc}")

    total = result["total_patched"]
    message = (
        f"{total} package(s) patché(s) avec succès."
        if total > 0
        else "Aucun patch appliqué — aucune version corrective disponible."
    )

    return RemediateResponse(
        patched=[PatchRecord(**p) for p in result["patched"]],
        unchanged=[UnchangedRecord(**u) for u in result["unchanged"]],
        total_patched=total,
        message=message,
    )
