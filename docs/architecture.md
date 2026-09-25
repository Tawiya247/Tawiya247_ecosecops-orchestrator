# Architecture — EcoSecOps Orchestrator

> Document finalisé — Tâche 8 (Polish final)

---

## Vue d'ensemble

**EcoSecOps Orchestrator** est une plateforme de gouvernance DevSecOps + GreenOps qui audite les dépendances open-source, mesure l'empreinte carbone du code selon ISO/IEC 21031:2024, et remédie automatiquement aux vulnérabilités et inefficacités énergétiques.

**Innovation principale :** Plutôt que de traiter la sécurité et la durabilité comme deux préoccupations séparées, EcoSecOps les fusionne dans un score unique de priorisation hybride — le **SPSC** — qui guide les décisions de remédiation par impact réel sur le binôme risque/carbone.

---

## Diagramme d'Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EcoSecOps Orchestrator                       │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
   ┌──────────▼──────────┐       ┌────────────▼────────────┐
   │   frontend/app.py   │       │   backend/main.py       │
   │   (Streamlit UI)    │◄─────►│   (FastAPI REST API)    │
   └─────────────────────┘       └────────────┬────────────┘
                                              │
              ┌───────────────────────────────┤
              │                               │
   ┌──────────▼──────────┐       ┌────────────▼────────────┐
   │    connectors/      │       │       core/             │
   │                     │       │                         │
   │  osv_client.py      │       │  metrics.py             │
   │  ├─ POST OSV.dev    │       │  ├─ calculate_sci()     │
   │  └─ Mock fallback   │       │  └─ calculate_spsc()    │
   │                     │       │                         │
   │  electricity_       │       │  remediator.py          │
   │  client.py          │       │  ├─ patch_requirements()│
   │  ├─ GET ElecMaps    │       │  ├─ parse_requirements()│
   │  └─ Mock fallback   │       │  └─ suggest_optims()    │
   └──────────┬──────────┘       └─────────────────────────┘
              │
   ┌──────────▼──────────┐       ┌─────────────────────────┐
   │   APIs Externes     │       │   backend/config.py     │
   │                     │       │                         │
   │  OSV.dev            │       │  settings singleton     │
   │  ElectricityMaps    │       │  (clés API, env vars)   │
   └─────────────────────┘       └─────────────────────────┘
```

---

## Description des Modules

### `backend/` — Application FastAPI

| Fichier | Rôle |
|---|---|
| `main.py` | Point d'entrée FastAPI. Expose `GET /health`, `POST /api/audit`, `POST /api/remediate`. Orchestre les connecteurs et les moteurs `core/` de façon asynchrone. |
| `config.py` | Singleton `settings` chargeant toutes les variables d'environnement via `python-dotenv`. Aucune valeur hardcodée — source unique de vérité pour les clés API. |

### `connectors/` — Clients HTTP Asynchrones

| Fichier | Rôle |
|---|---|
| `osv_client.py` | Client `httpx` async vers `POST https://api.osv.dev/v1/query`. Parse `requirements.txt`, retourne les vulnérabilités avec scores CVSS et versions fixées. Fallback mock : jinja2==2.11.2, CVSS=7.5, fixed=2.11.3. |
| `electricity_client.py` | Client `httpx` async vers `GET https://api.electricitymap.org/v3/carbon-intensity/latest`. Retourne l'intensité carbone en gCO₂e/kWh. Fallback mock si clé absente : `{"zone": "US-NY", "carbonIntensity": 210, "isMock": true}`. |

> **Règle d'architecture :** `connectors/` ne doit jamais importer depuis `backend/` — dépendance unidirectionnelle obligatoire.

### `core/` — Moteurs Mathématiques et Remédiation

| Fichier | Rôle |
|---|---|
| `metrics.py` | Implémente `calculate_sci()` (ISO/IEC 21031:2024) et `calculate_spsc()`. Constantes ALPHA=0.5, BETA=0.3, GAMMA=0.2. Guard contre R=0. |
| `remediator.py` | Patche les versions vulnérables dans `requirements.txt` via regex (`patch_requirements()`), génère des recommandations de réduction carbone par seuil SCI (`suggest_optimizations()`). Parser interne : `parse_requirements()`. |

### `frontend/` — Dashboard Streamlit

| Fichier | Rôle |
|---|---|
| `app.py` | Interface interactive. Sidebar paramétrable (zone, runtime, CPU). KPIs : SCI, intensité carbone (badge MOCK/LIVE), vulnérabilités, packages affectés. Tableau CVE par package avec SPSC. Bouton remédiation avec diff des patches appliqués. |

### `tests/` — Suite de Tests Pytest

| Fichier | Rôle |
|---|---|
| `test_connectors.py` | Tests unitaires `osv_client` et `electricity_client` avec mocks `respx` (zéro appel réseau réel). Couvre succès, erreur réseau, fallback mock. |
| `test_metrics.py` | Tests unitaires `calculate_sci()`, `calculate_spsc()`, `patch_requirements()`, `suggest_optimizations()`. Valeurs numériques vérifiées manuellement. |

---

## Formules Mathématiques

### SCI — Software Carbon Intensity (ISO/IEC 21031:2024)

```
SCI = ((E × I) + M) / R
```

| Paramètre | Description | Unité | Implémentation |
|---|---|---|---|
| `E` | Consommation énergétique opérationnelle | kWh | `runtime_hours × cpu_watts / 1000` |
| `I` | Intensité carbone du réseau électrique | gCO₂e/kWh | ElectricityMaps API ou mock=210 |
| `M` | Carbone embarqué du matériel | gCO₂e | Défaut statique : `0.05` |
| `R` | Unité fonctionnelle | — | Défaut : `1.0` (1 requête API) |

**Guard R≠0 :** `calculate_sci()` lève `ValueError` si `functional_unit == 0`.

### SPSC — Security-Carbon Priority Score

```
SPSC = α·CVSS + β·(I_actuel / I_ref) + γ·U_CPU
```

| Paramètre | Description | Défaut |
|---|---|---|
| `α` | Poids sécurité | `0.5` |
| `β` | Poids carbone | `0.3` |
| `γ` | Poids CPU | `0.2` |
| `CVSS` | Score vulnérabilité OSV | 0.0 – 10.0 |
| `I_ref` | Intensité carbone de référence | `300` gCO₂e/kWh |

Le SPSC est calculé au pire CVSS du package (worst-case). Les packages sont triés par SPSC décroissant dans les réponses d'audit.

---

## Flux de Données

### Audit — `POST /api/audit`

```
1. Client → POST /api/audit (requirements_path, zone, runtime, CPU)
2. Backend → asyncio.gather(
       osv_client.scan_requirements()    → Liste[{name, version, vulns[{cvss, fixed}]}]
       electricity_client.get_carbon()   → {carbonIntensity, zone, isMock}
   )
3. Backend → calculate_sci(E, I, M=0.05, R=1) → float SCI
4. Backend → calculate_spsc(cvss_max, I, I_ref=300, U_CPU) → float SPSC par package
5. Backend → suggest_optimizations(sci) → List[str]
6. Backend → AuditResponse JSON trié par SPSC décroissant → Client
```

### Remédiation — `POST /api/remediate`

```
1. Client → POST /api/remediate (requirements_path, zone)
2. Backend → osv_client.scan_requirements() → vulnérabilités avec fixed_version
3. Backend → remediator.patch_requirements(path, vulns) →
       - Lecture requirements.txt
       - Regex case-insensitive : pkg==old_version → pkg==fixed_version
       - Écriture du fichier patché
       - Retour {patched[], unchanged[], total_patched}
4. Backend → RemediateResponse → Client
```

---

## Choix Techniques

| Technologie | Raison |
|---|---|
| **FastAPI** | API REST moderne avec documentation Swagger auto-générée, support async natif, modèles Pydantic pour la validation des entrées/sorties |
| **httpx** | Client HTTP async compatible avec `asyncio`, `pytest-asyncio` et mockable via `respx` — indispensable pour les tests offline |
| **Streamlit** | Dashboard interactif minimal-code, idéal pour une démo hackathon convaincante en quelques heures |
| **python-dotenv** | Gestion standard des variables d'environnement sans hardcoding — pattern compatible avec tous les environnements CI/CD |
| **pytest + pytest-asyncio** | Couverture de tests mesurable, support des coroutines async, marqueur `@pytest.mark.asyncio` explicite |
| **respx** | Mock HTTP pour tests offline — intercepte `httpx.AsyncClient` sans modifier le code source des connecteurs |
| **asyncio.gather()** | Parallelisation OSV.dev + ElectricityMaps dans `/api/audit` — réduit la latence de ~50% par rapport aux appels séquentiels |

---

## Contraintes d'Architecture (Non-Négociables)

1. **Dépendance unidirectionnelle** : `connectors/` et `core/` n'importent jamais depuis `backend/`
2. **Pas de `os.getenv()` direct** dans `connectors/` ou `core/` — toujours via `settings` de `backend/config.py`
3. **Fallback mock obligatoire** sur chaque connecteur HTTP — le système doit fonctionner entièrement offline
4. **Guard R≠0** dans `calculate_sci()` — conformément à ISO/IEC 21031:2024
5. **Aucun secret dans le repo** — `.env` exclu via `.gitignore` et `.bobignore`

---

## Décisions d'Architecture

### Pourquoi un score SPSC et pas uniquement CVSS ?
CVSS seule ignore le contexte opérationnel. Un package CVSS=8 dans une région à énergie verte (France, 50 gCO₂e/kWh) est moins urgent qu'un CVSS=6 dans une région carbonée (US-MIDA, 450 gCO₂e/kWh) avec un CPU sous forte charge. Le SPSC intègre ces trois dimensions pour une remédiation guidée par l'impact réel.

### Pourquoi asyncio.gather() dans /api/audit ?
L'appel OSV.dev et l'appel ElectricityMaps sont indépendants — les lancer en parallèle divise la latence perçue de moitié (~500ms vs ~1s en séquentiel sur des connexions normales).

### Pourquoi regex et non AST pour patcher requirements.txt ?
`requirements.txt` n'est pas du code Python — c'est un format texte. Le parsing AST est inutile ici. Une substitution regex case-insensitive sur `pkg==version` est plus simple, plus rapide et sans dépendance externe.

---

*Architecture finalisée par IBM Bob 2.0 — Hackathon IBM Bob 2.0*
