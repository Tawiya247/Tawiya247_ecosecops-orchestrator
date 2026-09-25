"""
tests/test_metrics.py — Tests des métriques SCI, SPSC et remediator
EcoSecOps Orchestrator — Hackathon IBM Bob 2.0
"""

import pytest

from core.metrics import calculate_sci, calculate_spsc
from core.remediator import parse_requirements, patch_requirements, suggest_optimizations


# ===========================================================================
# Tests calculate_sci()
# ===========================================================================


def test_calculate_sci_basic():
    """SCI(E=0.01, I=240, M=0.05, R=1.0) = (0.01×240 + 0.05) / 1.0 = 2.45"""
    result = calculate_sci(energy_kwh=0.01, carbon_intensity=240, embodied_carbon=0.05, functional_unit=1.0)
    assert result == pytest.approx(2.45, abs=1e-9)


def test_calculate_sci_custom_params():
    """SCI(E=0.1, I=200, M=0.05, R=10.0) = (0.1×200 + 0.05) / 10.0 = 2.005"""
    result = calculate_sci(energy_kwh=0.1, carbon_intensity=200, embodied_carbon=0.05, functional_unit=10.0)
    assert result == pytest.approx(2.005, abs=1e-9)


def test_calculate_sci_default_embodied_carbon():
    """Appel sans M ni R : (1.0×100.0 + 0.05) / 1.0 = 100.05"""
    result = calculate_sci(energy_kwh=1.0, carbon_intensity=100.0)
    assert result == pytest.approx(100.05, abs=1e-9)


def test_calculate_sci_raises_on_zero_functional_unit():
    """functional_unit=0 doit lever ValueError."""
    with pytest.raises(ValueError):
        calculate_sci(1.0, 100.0, functional_unit=0)


# ===========================================================================
# Tests calculate_spsc()
# ===========================================================================


def test_calculate_spsc_reference_values():
    """SPSC(CVSS=7.5, I_act=210, I_ref=300, U_CPU=0.5) = 3.75 + 0.21 + 0.10 = 4.06"""
    result = calculate_spsc(cvss=7.5, current_intensity=210, reference_intensity=300, cpu_utilization=0.5)
    assert result == pytest.approx(4.06, abs=1e-9)


def test_calculate_spsc_zero_cvss():
    """SPSC(CVSS=0.0, I_act=300, I_ref=300, U_CPU=0.0) = 0.0 + 0.3×1.0 + 0.0 = 0.3"""
    result = calculate_spsc(cvss=0.0, current_intensity=300, reference_intensity=300, cpu_utilization=0.0)
    assert result == pytest.approx(0.3, abs=1e-9)


def test_calculate_spsc_max_cvss():
    """SPSC(CVSS=10.0, I_act=0.0, I_ref=300, U_CPU=1.0) = 5.0 + 0.0 + 0.2 = 5.2"""
    result = calculate_spsc(cvss=10.0, current_intensity=0.0, reference_intensity=300, cpu_utilization=1.0)
    assert result == pytest.approx(5.2, abs=1e-9)


def test_calculate_spsc_default_reference_intensity():
    """Appel sans I_ref ni U_CPU : 0.5×5.0 + 0.3×(150/300) + 0.2×0.0 = 2.5 + 0.15 = 2.65"""
    result = calculate_spsc(cvss=5.0, current_intensity=150.0)
    assert result == pytest.approx(2.65, abs=1e-9)


# ===========================================================================
# Tests parse_requirements()
# ===========================================================================


def test_parse_requirements_basic(tmp_path):
    """Parse les lignes package==version et ignore les commentaires et >= ."""
    req = tmp_path / "requirements.txt"
    req.write_text(
        "# commentaire\n"
        "jinja2==2.11.2\n"
        "requests>=2.28.0\n"
        "flask==2.0.1\n",
        encoding="utf-8",
    )
    result = parse_requirements(str(req))
    assert len(result) == 2
    assert result[0]["name"] == "jinja2"
    assert result[0]["version"] == "2.11.2"
    assert result[1]["name"] == "flask"
    assert result[1]["version"] == "2.0.1"


def test_parse_requirements_file_not_found():
    """Lève FileNotFoundError si le fichier est absent."""
    with pytest.raises(FileNotFoundError):
        parse_requirements("/nonexistent/requirements.txt")


def test_parse_requirements_empty_file(tmp_path):
    """Fichier vide → liste vide."""
    req = tmp_path / "requirements.txt"
    req.write_text("", encoding="utf-8")
    result = parse_requirements(str(req))
    assert result == []


# ===========================================================================
# Tests patch_requirements()
# ===========================================================================


def test_patch_requirements_applies_fix(tmp_path):
    """patch_requirements remplace la version vulnérable par la version fixée."""
    req = tmp_path / "requirements.txt"
    req.write_text("jinja2==2.11.2\nrequests>=2.28.0\n", encoding="utf-8")

    vulnerabilities = [
        {
            "name": "jinja2",
            "version": "2.11.2",
            "ecosystem": "PyPI",
            "vulns": [
                {
                    "id": "GHSA-fe52-489u-72pt",
                    "summary": "HTML injection",
                    "cvss_score": 7.5,
                    "fixed_version": "2.11.3",
                }
            ],
            "is_mock": True,
        }
    ]

    result = patch_requirements(str(req), vulnerabilities)

    assert result["total_patched"] == 1
    assert result["patched"][0]["name"] == "jinja2"
    assert result["patched"][0]["old_version"] == "2.11.2"
    assert result["patched"][0]["new_version"] == "2.11.3"

    updated = req.read_text(encoding="utf-8")
    assert "jinja2==2.11.3" in updated
    assert "jinja2==2.11.2" not in updated


def test_patch_requirements_no_fixed_version(tmp_path):
    """Si aucune fixed_version disponible → package va dans unchanged."""
    req = tmp_path / "requirements.txt"
    req.write_text("flask==2.0.1\n", encoding="utf-8")

    vulnerabilities = [
        {
            "name": "flask",
            "version": "2.0.1",
            "ecosystem": "PyPI",
            "vulns": [
                {
                    "id": "FAKE-001",
                    "summary": "fake",
                    "cvss_score": 5.0,
                    "fixed_version": "",
                }
            ],
            "is_mock": False,
        }
    ]

    result = patch_requirements(str(req), vulnerabilities)
    assert result["total_patched"] == 0
    assert len(result["unchanged"]) == 1
    assert result["unchanged"][0]["name"] == "flask"


def test_patch_requirements_already_fixed(tmp_path):
    """Si version courante == version fixée → package va dans unchanged."""
    req = tmp_path / "requirements.txt"
    req.write_text("jinja2==2.11.3\n", encoding="utf-8")

    vulnerabilities = [
        {
            "name": "jinja2",
            "version": "2.11.3",
            "ecosystem": "PyPI",
            "vulns": [{"id": "X", "summary": "y", "cvss_score": 7.5, "fixed_version": "2.11.3"}],
            "is_mock": False,
        }
    ]

    result = patch_requirements(str(req), vulnerabilities)
    assert result["total_patched"] == 0
    assert len(result["unchanged"]) == 1


def test_patch_requirements_package_not_in_file(tmp_path):
    """Package dans vulnerabilities mais absent du fichier → unchanged."""
    req = tmp_path / "requirements.txt"
    req.write_text("flask==2.0.1\n", encoding="utf-8")

    vulnerabilities = [
        {
            "name": "jinja2",
            "version": "2.11.2",
            "ecosystem": "PyPI",
            "vulns": [{"id": "X", "summary": "y", "cvss_score": 7.5, "fixed_version": "2.11.3"}],
            "is_mock": True,
        }
    ]

    result = patch_requirements(str(req), vulnerabilities)
    assert result["total_patched"] == 0
    assert len(result["unchanged"]) == 1


def test_patch_requirements_file_not_found():
    """Lève FileNotFoundError si le fichier est absent."""
    with pytest.raises(FileNotFoundError):
        patch_requirements("/nonexistent/req.txt", [])


# ===========================================================================
# Tests suggest_optimizations()
# ===========================================================================


def test_suggest_optimizations_excellent():
    """SCI < 0.1 → message positif uniquement."""
    result = suggest_optimizations(0.05)
    assert len(result) >= 1
    assert any("excellent" in r.lower() or "good" in r.lower() for r in result)


def test_suggest_optimizations_moderate():
    """0.1 <= SCI < 0.5 → recommandations modérées (cache, batch...)."""
    result = suggest_optimizations(0.25)
    assert len(result) >= 1
    # Au moins une recommandation concrète
    full = " ".join(result).lower()
    assert any(word in full for word in ["cache", "batch", "profile", "reduc"])


def test_suggest_optimizations_urgent():
    """SCI >= 0.5 → recommandations urgentes (migration, scheduling...)."""
    result = suggest_optimizations(1.0)
    assert len(result) >= 3
    full = " ".join(result).lower()
    assert "urgent" in full or "migrat" in full or "schedul" in full


def test_suggest_optimizations_boundary_exact_01():
    """SCI == 0.1 doit retourner des recommandations modérées (pas excellent)."""
    result = suggest_optimizations(0.1)
    full = " ".join(result).lower()
    # Ne doit pas contenir le message "excellent"
    assert "excellent" not in full


def test_suggest_optimizations_boundary_exact_05():
    """SCI == 0.5 doit retourner des recommandations urgentes."""
    result = suggest_optimizations(0.5)
    full = " ".join(result).lower()
    assert "urgent" in full or "migrat" in full
