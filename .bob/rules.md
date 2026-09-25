# EcoSecOps Orchestrator — Bob Governance Rules
# Project: IBM Bob 2.0 Hackathon
# Version: 1.0.0

## 1. Règles de Sécurité (CRITIQUES — non négociables)

- **JAMAIS** commiter `.env`, `*.key`, `credentials.json`, `*.pem`, `*.p12` dans Git.
- Toutes les clés API (ELECTRICITY_MAPS_API_KEY, etc.) doivent être lues **uniquement** depuis les variables d'environnement via `backend/config.py`.
- `.env` DOIT figurer dans `.gitignore` ET `.bobignore` — IBM surveille les dépôts GitHub.
- Utiliser `.env.example` (sans valeurs réelles) comme référence documentaire des variables requises.
- Ne jamais hardcoder une valeur secrète dans le code source, même en commentaire.

## 2. Règles de Workflow

- **Une tâche = une session Bob** : chaque tâche du plan ecosecops-plan.md est exécutée dans une session dédiée.
- L'agent principal orchestre ; les sous-agents ont un périmètre strict (un fichier cible par sous-agent).
- Les sous-agents reçoivent uniquement le contexte minimal nécessaire (schéma API ou formule concernée).
- Toujours valider avec `pytest --cov` avant de considérer une tâche comme terminée.
- Les tâches 3 et 4 (metrics.py + remediator.py) peuvent être parallélisées.

## 3. Règles de Qualité de Code

- **Type hints** obligatoires sur toutes les fonctions publiques.
- **Docstrings** obligatoires sur toutes les fonctions (format Google ou NumPy).
- Couverture de tests : objectif **>80%** (vérifiable avec `pytest --cov=. --cov-report=term-missing`).
- Architecture modulaire : aucun import circulaire entre `connectors/`, `core/`, `backend/`.
- Les connecteurs (`connectors/`) ne doivent jamais importer depuis `backend/`.
- Chaque client HTTP doit avoir un **fallback mock** robuste (mode offline garanti).

## 4. Règles de Documentation

- `README.md` : description, architecture, installation, utilisation, formules SCI/SPSC.
- `docs/architecture.md` : diagramme textuel et justification des choix techniques.
- Chaque endpoint FastAPI doit avoir une description dans le schéma Pydantic (utilisée par Swagger).
- Les formules mathématiques doivent référencer le standard **ISO/IEC 21031:2024**.

## 5. Règles des Captures de Session Bob (Preuves Hackathon)

- 4 captures obligatoires dans `bob_sessions/` avec les noms exacts :
  - `01_init_repository_scan.png` — après `/init`
  - `02_connectors_generation.png` — après Tâche 2
  - `03_core_metrics_refactoring.png` — après Tâche 3/4
  - `04_tests_and_summary.png` — après Tâche 7
- Aucune clé API, token ou secret ne doit être visible sur les captures.
- Flouter toute donnée sensible avant de commiter dans `bob_sessions/`.

## 6. Architecture Interdite

- Pas de déploiement cloud dans le scope hackathon.
- Pas de support multi-langage (Python uniquement).
- Pas d'intégration CI/CD automatique.
- Pas de dépendances externes non listées dans `requirements.txt`.
