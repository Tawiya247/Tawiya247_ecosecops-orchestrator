"""
EcoSecOps Orchestrator — Métriques carbone et sécurité.

Implémente les formules SCI (ISO/IEC 21031:2024) et SPSC.
"""

# ---------------------------------------------------------------------------
# Constantes SPSC
# ---------------------------------------------------------------------------

ALPHA: float = 0.5  # Poids du score de vulnérabilité (CVSS)
BETA: float = 0.3   # Poids de l'intensité carbone relative
GAMMA: float = 0.2  # Poids de l'utilisation CPU


def calculate_sci(
    energy_kwh: float,
    carbon_intensity: float,
    embodied_carbon: float = 0.05,
    functional_unit: float = 1.0,
) -> float:
    """Calcule le Software Carbon Intensity (SCI) selon ISO/IEC 21031:2024.

    Formule : SCI = ((E × I) + M) / R

    Args:
        energy_kwh (float): Énergie opérationnelle consommée, en kWh.
        carbon_intensity (float): Intensité carbone du réseau électrique,
            en gCO₂e/kWh.
        embodied_carbon (float): Carbone embarqué du matériel, en gCO₂e.
            Défaut : 0.05.
        functional_unit (float): Unité fonctionnelle R (dénominateur).
            Défaut : 1.0. Doit être différent de zéro.

    Returns:
        float: Score SCI en gCO₂e par unité fonctionnelle.

    Raises:
        ValueError: Si ``functional_unit`` est égal à 0 (division par zéro
            interdite conformément à ISO/IEC 21031:2024).

    References:
        ISO/IEC 21031:2024 — Software Carbon Intensity (SCI) Specification.
    """
    if functional_unit == 0:
        raise ValueError(
            "functional_unit ne peut pas être nul (ISO/IEC 21031:2024 : "
            "R doit être une unité fonctionnelle non nulle)."
        )

    return ((energy_kwh * carbon_intensity) + embodied_carbon) / functional_unit


def calculate_spsc(
    cvss: float,
    current_intensity: float,
    reference_intensity: float = 300.0,
    cpu_utilization: float = 0.0,
) -> float:
    """Calcule le Security-Carbon Priority Score (SPSC).

    Formule : SPSC = α·CVSS + β·(I_actuel / I_ref) + γ·U_CPU

    Combine le risque de sécurité (score CVSS OSV), la pression carbone
    courante relative à une référence, et l'utilisation CPU normalisée afin
    de prioriser les actions de remédiation en tenant compte de leur empreinte
    environnementale.

    Args:
        cvss (float): Score de vulnérabilité OSV, compris entre 0.0 et 10.0.
        current_intensity (float): Intensité carbone courante du réseau,
            en gCO₂e/kWh.
        reference_intensity (float): Intensité carbone de référence utilisée
            pour la normalisation, en gCO₂e/kWh. Défaut : 300.0.
        cpu_utilization (float): Utilisation CPU normalisée, entre 0.0
            (inactif) et 1.0 (100 %). Défaut : 0.0.

    Returns:
        float: Score SPSC (sans unité) combinant vulnérabilité, carbone
            et charge CPU.
    """
    return (
        ALPHA * cvss
        + BETA * (current_intensity / reference_intensity)
        + GAMMA * cpu_utilization
    )
