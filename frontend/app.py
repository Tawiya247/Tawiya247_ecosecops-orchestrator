"""
frontend/app.py — Dashboard Streamlit
EcoSecOps Orchestrator — Hackathon IBM Bob 2.0

Interface interactive affichant les scores SCI, les CVEs détectées,
l'intensité carbone et permettant de déclencher la remédiation.

Démarrage : streamlit run frontend/app.py
Prérequis  : Le backend FastAPI doit tourner sur BACKEND_URL (défaut : http://localhost:8000)
"""

import os
import httpx
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="EcoSecOps Orchestrator",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar — Paramètres
# ---------------------------------------------------------------------------

st.sidebar.title("⚙️ Paramètres")

requirements_path = st.sidebar.text_input(
    "Chemin requirements.txt",
    value="requirements.txt",
    help="Chemin relatif ou absolu vers le fichier requirements.txt à auditer.",
)

zone = st.sidebar.selectbox(
    "Zone carbone (ElectricityMaps)",
    options=["US-NY", "FR", "DE", "GB", "US-CAL-CISO", "AU-NSW"],
    index=0,
    help="Zone géographique pour l'intensité carbone du réseau électrique.",
)

runtime_hours = st.sidebar.number_input(
    "Durée d'exécution (heures)",
    min_value=0.01,
    max_value=24.0,
    value=1.0,
    step=0.1,
    help="Durée estimée d'exécution pour le calcul SCI.",
)

cpu_watts = st.sidebar.number_input(
    "Consommation CPU (watts)",
    min_value=1.0,
    max_value=500.0,
    value=10.0,
    step=1.0,
    help="Puissance CPU consommée pour le calcul de l'énergie.",
)

cpu_utilization = st.sidebar.slider(
    "Utilisation CPU (%)",
    min_value=0,
    max_value=100,
    value=50,
    step=5,
    help="Utilisation CPU normalisée pour le score SPSC.",
) / 100.0

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("🌿 EcoSecOps Orchestrator")
st.caption(
    "Plateforme de gouvernance DevSecOps + GreenOps — "
    "Hackathon IBM Bob 2.0 | ISO/IEC 21031:2024"
)
st.divider()

# ---------------------------------------------------------------------------
# Helpers HTTP
# ---------------------------------------------------------------------------


def call_audit(path: str, zone: str, runtime_hours: float, cpu_watts: float, cpu_util: float) -> dict:
    """Appelle POST /api/audit sur le backend FastAPI."""
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            f"{BACKEND_URL}/api/audit",
            json={
                "requirements_path": path,
                "zone": zone,
                "runtime_hours": runtime_hours,
                "cpu_watts": cpu_watts,
                "cpu_utilization": cpu_util,
            },
        )
        response.raise_for_status()
        return response.json()


def call_remediate(path: str, zone: str) -> dict:
    """Appelle POST /api/remediate sur le backend FastAPI."""
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            f"{BACKEND_URL}/api/remediate",
            json={"requirements_path": path, "zone": zone},
        )
        response.raise_for_status()
        return response.json()


# ---------------------------------------------------------------------------
# Section principale — Audit
# ---------------------------------------------------------------------------

col_btn, col_spacer = st.columns([1, 4])
with col_btn:
    run_audit = st.button("🔍 Lancer l'audit", type="primary", use_container_width=True)

if run_audit:
    with st.spinner("Audit en cours — scan OSV.dev + ElectricityMaps…"):
        try:
            data = call_audit(requirements_path, zone, runtime_hours, cpu_watts, cpu_utilization)
            st.session_state["audit_data"] = data
            st.session_state["audit_path"] = requirements_path
            st.session_state["audit_zone"] = zone
        except httpx.ConnectError:
            st.error(
                f"❌ Impossible de joindre le backend sur `{BACKEND_URL}`. "
                "Assurez-vous que le serveur FastAPI est démarré."
            )
        except httpx.HTTPStatusError as exc:
            st.error(f"❌ Erreur backend ({exc.response.status_code}) : {exc.response.text}")
        except Exception as exc:
            st.error(f"❌ Erreur inattendue : {exc}")

# ---------------------------------------------------------------------------
# Affichage des résultats d'audit
# ---------------------------------------------------------------------------

if "audit_data" in st.session_state:
    data = st.session_state["audit_data"]

    # --- KPI Row ---
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    sci = data.get("sci", 0)
    carbon_intensity = data.get("carbon_intensity", 0)
    carbon_is_mock = data.get("carbon_is_mock", True)
    total_vulns = data.get("total_vulnerabilities", 0)
    packages = data.get("packages", [])
    n_vulnerable = sum(1 for p in packages if p.get("vulns"))

    with kpi1:
        sci_delta = "↑ Élevé" if sci >= 0.5 else ("↔ Modéré" if sci >= 0.1 else "↓ Faible")
        st.metric(
            label="🌱 Score SCI",
            value=f"{sci:.4f}",
            delta=sci_delta,
            delta_color="inverse",
            help="Software Carbon Intensity (ISO/IEC 21031:2024). Plus bas = mieux.",
        )

    with kpi2:
        mock_badge = " 🔸 MOCK" if carbon_is_mock else " ✅ LIVE"
        st.metric(
            label=f"⚡ Intensité carbone{mock_badge}",
            value=f"{carbon_intensity} gCO₂e/kWh",
            help="Intensité carbone du réseau électrique pour la zone sélectionnée.",
        )

    with kpi3:
        st.metric(
            label="🔒 Vulnérabilités",
            value=total_vulns,
            help="Nombre total de CVEs détectées.",
        )

    with kpi4:
        st.metric(
            label="📦 Packages affectés",
            value=f"{n_vulnerable} / {len(packages)}",
            help="Nombre de packages avec au moins une vulnérabilité.",
        )

    st.divider()

    # --- Recommandations SCI ---
    optimizations = data.get("optimizations", [])
    if optimizations:
        with st.expander("💡 Recommandations de réduction carbone", expanded=(sci >= 0.1)):
            for rec in optimizations:
                st.markdown(f"- {rec}")

    # --- Tableau CVE ---
    st.subheader("🛡️ Rapport de vulnérabilités par package")

    if not packages:
        st.info("Aucun package détecté dans le fichier requirements.txt.")
    else:
        for pkg in packages:
            vulns = pkg.get("vulns", [])
            mock_tag = " *(mock)*" if pkg.get("is_mock") else ""
            spsc = pkg.get("spsc", 0.0)

            severity_color = "🔴" if spsc >= 4.0 else ("🟠" if spsc >= 2.0 else "🟢")
            header = (
                f"{severity_color} **{pkg['name']}** `{pkg['version']}`{mock_tag} "
                f"— SPSC: `{spsc:.4f}`"
            )

            with st.expander(header, expanded=(len(vulns) > 0)):
                if not vulns:
                    st.success("✅ Aucune vulnérabilité détectée.")
                else:
                    rows = []
                    for v in vulns:
                        cvss = v.get("cvss_score", 0.0)
                        severity = "CRITIQUE" if cvss >= 9.0 else (
                            "HAUTE" if cvss >= 7.0 else (
                                "MOYENNE" if cvss >= 4.0 else "FAIBLE"
                            )
                        )
                        rows.append({
                            "ID": v.get("id", "—"),
                            "Résumé": v.get("summary", "—"),
                            "CVSS": f"{cvss:.1f}",
                            "Sévérité": severity,
                            "Version fixée": v.get("fixed_version", "—"),
                        })
                    st.table(rows)

    st.divider()

    # --- Bouton Remédiation ---
    st.subheader("🔧 Remédiation automatique")
    st.markdown(
        "Applique automatiquement les patches de sécurité sur `requirements.txt` "
        "en remplaçant les versions vulnérables par les versions correctives recommandées par OSV."
    )

    if st.button("⚡ Exécuter la remédiation", type="secondary", use_container_width=False):
        with st.spinner("Application des patches…"):
            try:
                rem_data = call_remediate(
                    st.session_state.get("audit_path", requirements_path),
                    st.session_state.get("audit_zone", zone),
                )

                total_patched = rem_data.get("total_patched", 0)
                if total_patched > 0:
                    st.success(f"✅ {rem_data.get('message', '')}")
                else:
                    st.info(f"ℹ️ {rem_data.get('message', 'Aucun patch appliqué.')}")

                # Affichage du diff
                patched = rem_data.get("patched", [])
                unchanged = rem_data.get("unchanged", [])

                if patched:
                    st.markdown("**Packages patchés :**")
                    patch_rows = [
                        {
                            "Package": p["name"],
                            "Ancienne version": p["old_version"],
                            "Nouvelle version": p["new_version"],
                        }
                        for p in patched
                    ]
                    st.table(patch_rows)

                if unchanged:
                    with st.expander(f"Packages non patchés ({len(unchanged)})"):
                        for u in unchanged:
                            st.markdown(f"- **{u['name']}** : {u['reason']}")

                # Invalider le cache d'audit pour forcer un re-audit
                if "audit_data" in st.session_state:
                    del st.session_state["audit_data"]
                    st.info("♻️ Relancez l'audit pour voir les résultats mis à jour.")

            except httpx.ConnectError:
                st.error(
                    f"❌ Impossible de joindre le backend sur `{BACKEND_URL}`."
                )
            except httpx.HTTPStatusError as exc:
                st.error(f"❌ Erreur backend ({exc.response.status_code}) : {exc.response.text}")
            except Exception as exc:
                st.error(f"❌ Erreur inattendue : {exc}")

else:
    st.info("👈 Configurez les paramètres dans la barre latérale, puis cliquez sur **Lancer l'audit**.")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.divider()
st.caption(
    "EcoSecOps Orchestrator — Hackathon IBM Bob 2.0 | "
    "Développé avec IBM Bob 2.0 | "
    "Standard ISO/IEC 21031:2024 (SCI)"
)
