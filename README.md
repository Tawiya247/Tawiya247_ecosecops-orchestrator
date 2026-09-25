# EcoSecOps Orchestrator

> **Hackathon IBM Bob 2.0** — Plateforme de gouvernance DevSecOps + GreenOps

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/Tests-pytest-orange)](https://pytest.org/)
[![Coverage](https://img.shields.io/badge/Coverage-%3E80%25-brightgreen)]()
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Standard](https://img.shields.io/badge/Standard-ISO%2FIEC%2021031%3A2024-blueviolet)]()

---

## Description

**EcoSecOps Orchestrator** est une plateforme d'audit et de remédiation automatique qui unifie la sécurité logicielle et la durabilité environnementale dans un seul système de gouvernance agentic.

Elle répond à une question que personne ne pose encore : *"Mon code est-il sécurisé **et** vert ?"*

### Ce qu'il fait

- 🔒 **Audit de sécurité** : Détecte les vulnérabilités open-source via [OSV.dev](https://osv.dev) et calcule les scores CVSS pour chaque dépendance de `requirements.txt`
- 🌱 **Mesure carbone** : Calcule le **Software Carbon Intensity (SCI)** conforme ISO/IEC 21031:2024 en temps réel via [ElectricityMaps](https://electricitymaps.com)
- ⚡ **Score de priorisation hybride** : Le score **SPSC** combine CVSS, intensité carbone et utilisation CPU pour ordonner les remédiations par impact réel
- 🔧 **Remédiation automatique** : Patche les versions vulnérables dans `requirements.txt` et génère des recommandations de réduction carbone
- 📊 **Dashboard interactif** : Interface Streamlit avec métriques live, tableau CVE et bouton de remédiation en un clic

---

## Architecture

```
Frontend (Streamlit) ←→ Backend (FastAPI)
                              │
              ┌───────────────┼───────────────┐
              │               │               │
      connectors/         connectors/       core/
      osv_client.py    electricity_client  metrics.py
      (OSV.dev API)    (ElectricityMaps)   remediator.py
```

Voir [`docs/architecture.md`](docs/architecture.md) pour le diagramme complet et les choix techniques.

---

## Formules Mathématiques

### SCI — Software Carbon Intensity (ISO/IEC 21031:2024)

```
SCI = ((E × I) + M) / R
```

| Paramètre | Description | Unité | Défaut |
|---|---|---|---|
| `E` | Énergie opérationnelle (`runtime_hours × cpu_watts / 1000`) | kWh | — |
| `I` | Intensité carbone du réseau électrique | gCO₂e/kWh | live ou 210 (mock) |
| `M` | Carbone embarqué du matériel | gCO₂e | `0.05` |
| `R` | Unité fonctionnelle (requête API, exécution…) | — | `1.0` |

### SPSC — Security-Carbon Priority Score

```
SPSC = 0.5 × CVSS + 0.3 × (I_actuel / I_ref) + 0.2 × U_CPU
```

| Paramètre | Description | Défaut |
|---|---|---|
| `CVSS` | Score de vulnérabilité OSV | 0.0 – 10.0 |
| `I_actuel` | Intensité carbone courante | gCO₂e/kWh |
| `I_ref` | Intensité carbone de référence | `300` gCO₂e/kWh |
| `U_CPU` | Utilisation CPU normalisée | 0.0 – 1.0 |
| `α / β / γ` | Poids sécurité / carbone / CPU | `0.5 / 0.3 / 0.2` |

---

## Prérequis

- Python **3.11+**
- `pip` (ou `pip3`)
- *(optionnel)* Clé API [ElectricityMaps](https://api.electricitymap.org/) pour les données carbone live

---

## Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/<votre-org>/ecosecops-orchestrator.git
cd ecosecops-orchestrator

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env et renseigner ELECTRICITY_MAPS_API_KEY (facultatif — fallback mock sinon)
```

---

## Démarrage

### Backend FastAPI

```bash
uvicorn backend.main:app --reload --port 8000
```

Documentation Swagger auto-générée : **http://localhost:8000/docs**

### Frontend Streamlit

```bash
streamlit run frontend/app.py
```

Dashboard interactif : **http://localhost:8501**

> ℹ️ Le frontend nécessite que le backend soit démarré. Sans clé API ElectricityMaps, les données carbone utilisent le fallback mock (badge 🔸 MOCK visible dans le dashboard).

---

## API Endpoints

### `GET /health`

Vérification du statut du service.

**Réponse :**
```json
{"status": "ok"}
```

---

### `POST /api/audit`

Audite un fichier `requirements.txt`, détecte les CVEs via OSV.dev, mesure l'intensité carbone, et calcule les scores SCI et SPSC.

**Corps de la requête :**
```json
{
  "requirements_path": "requirements.txt",
  "zone": "US-NY",
  "runtime_hours": 1.0,
  "cpu_watts": 10.0,
  "cpu_utilization": 0.5
}
```

**Réponse :**
```json
{
  "sci": 0.002155,
  "carbon_intensity": 210.0,
  "carbon_is_mock": true,
  "zone": "US-NY",
  "total_vulnerabilities": 1,
  "packages": [
    {
      "name": "jinja2",
      "version": "2.11.2",
      "ecosystem": "PyPI",
      "is_mock": true,
      "spsc": 3.91,
      "vulns": [
        {
          "id": "GHSA-fe52-489u-72pt",
          "summary": "HTML injection in Jinja2",
          "cvss_score": 7.5,
          "fixed_version": "2.11.3"
        }
      ]
    }
  ],
  "optimizations": ["Reduce unnecessary API or network requests..."]
}
```

---

### `POST /api/remediate`

Applique automatiquement les patches de sécurité sur `requirements.txt` en remplaçant les versions vulnérables par les versions correctives recommandées par OSV.

**Corps de la requête :**
```json
{
  "requirements_path": "requirements.txt",
  "zone": "US-NY"
}
```

**Réponse :**
```json
{
  "patched": [
    {"name": "jinja2", "old_version": "2.11.2", "new_version": "2.11.3"}
  ],
  "unchanged": [],
  "total_patched": 1,
  "message": "1 package(s) patché(s) avec succès."
}
```

---

## Tests

```bash
# Lancer tous les tests
pytest

# Avec rapport de couverture (objectif : >80%)
pytest --cov=. --cov-report=term-missing

# Test unitaire ciblé
pytest tests/test_metrics.py::test_calculate_sci -v
```

> Tous les tests fonctionnent **en mode offline** — aucun vrai appel API n'est effectué. Les appels HTTP sont mockés via `respx`.

---

## Mode Offline / Fallbacks Mock

Le système fonctionne entièrement sans clé API :

| Composant | Fallback Mock |
|---|---|
| OSV.dev | `jinja2==2.11.2`, CVSS=7.5, fixed=`2.11.3` |
| ElectricityMaps | `{"zone": "US-NY", "carbonIntensity": 210, "isMock": true}` |

---

## Structure du Projet

```
ecosecops-orchestrator/
├── .bob/rules.md              # Règles de gouvernance IBM Bob 2.0
├── .env.example               # Template des variables d'environnement
├── requirements.txt           # Dépendances Python
├── backend/
│   ├── main.py                # Application FastAPI (3 endpoints)
│   └── config.py              # Chargement des variables d'environnement
├── connectors/
│   ├── osv_client.py          # Client OSV.dev async (CVEs + CVSS)
│   └── electricity_client.py  # Client ElectricityMaps async (gCO₂e/kWh)
├── core/
│   ├── metrics.py             # Calculs SCI (ISO/IEC 21031:2024) et SPSC
│   └── remediator.py          # Remédiation automatique requirements.txt
├── frontend/
│   └── app.py                 # Dashboard Streamlit interactif
├── tests/
│   ├── test_connectors.py     # Tests des connecteurs (mocks respx)
│   └── test_metrics.py        # Tests formules SCI, SPSC, remediator
├── docs/
│   ├── architecture.md        # Architecture et choix techniques
│   ├── problem_statement.md   # Énoncé du problème (<500 mots)
│   └── usage_statement.md     # Déclaration d'usage (<500 mots)
└── bob_sessions/              # Captures de session IBM Bob 2.0
```

---

## Variables d'Environnement

Copier `.env.example` → `.env` et renseigner les valeurs :

| Variable | Description | Défaut |
|---|---|---|
| `ELECTRICITY_MAPS_API_KEY` | Clé API ElectricityMaps (optionnelle) | `""` (mode mock) |
| `OSV_API_URL` | Endpoint OSV.dev | `https://api.osv.dev/v1/query` |
| `APP_ENV` | Environnement (`development`/`production`/`test`) | `development` |
| `PORT` | Port du serveur FastAPI | `8000` |
| `BACKEND_URL` | URL du backend pour le frontend | `http://localhost:8000` |

---

## Hackathon IBM Bob 2.0

Ce projet a été développé avec **IBM Bob 2.0** comme co-développeur IA dans le cadre du Hackathon IBM Bob 2.0 sur [lablab.ai](https://lablab.ai).

IBM Bob 2.0 a été utilisé pour :
- La planification multi-tâches (`/plan` mode)
- La génération des connecteurs, moteurs mathématiques et tests (`agent` mode)
- La revue de code et l'orchestration des sous-agents spécialisés

Les captures de session Bob sont disponibles dans [`bob_sessions/`](bob_sessions/).

---

*Built with ❤️ and IBM Bob 2.0*
