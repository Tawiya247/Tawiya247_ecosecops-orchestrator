# Plan de travail — EcoSecOps Orchestrator
**Hackathon IBM Bob 2.0**
**Statut global :** En cours de planification

---

## Vue d'ensemble

**Objectif :** Construire EcoSecOps Orchestrator, une plateforme de gouvernance DevSecOps + GreenOps qui audite les dépendances open-source (OSV.dev), mesure l'empreinte carbone du code (SCI — ISO/IEC 21031:2024) via ElectricityMaps, et remédie automatiquement aux vulnérabilités et inefficacités énergétiques via un score de priorisation hybride (SPSC).

**Périmètre :**
- Backend FastAPI exposant 3 endpoints d'audit et de remédiation
- Connecteurs vers OSV.dev et ElectricityMaps avec fallbacks mock
- Moteurs mathématiques SCI et SPSC
- Moteur de remédiation AST
- Dashboard Streamlit interactif
- Suite de tests Pytest (>80% de couverture)

**Non-périmètre :**
- Intégration CI/CD automatique
- Déploiement cloud (hors scope hackathon)
- Support multi-langage (Python uniquement pour ce hackathon)

---

## Stratégie de sous-agents Bob

Pour optimiser la fenêtre de contexte et paralléliser le travail, certaines tâches seront déléguées à des **sous-agents Bob spécialisés**. Chaque sous-agent a un périmètre strict et retourne un résumé à l'agent principal.

| Sous-agent | Responsabilité | Tâches concernées |
|---|---|---|
| **Agent Connectors** | Implémenter osv_client.py et electricity_client.py | Tâche 2 |
| **Agent Math Engine** | Implémenter metrics.py (SCI + SPSC) | Tâche 3 |
| **Agent Remediator** | Implémenter remediator.py (AST patching) | Tâche 4 |
| **Agent Tests** | Écrire tous les tests Pytest avec mocks | Tâche 7 |
| **Agent Docs** | Rédiger README, architecture.md, problem/usage statements | Tâche 8 |

> **Règle d'or des sous-agents :** Chaque sous-agent reçoit uniquement le contexte dont il a besoin (son fichier cible + les schémas API ou formules concernés). Il ne voit jamais tout le codebase. Cela préserve la fenêtre de contexte principale pour l'orchestration.

---

## Rappels captures d'écran — Guide pas à pas

> ⚠️ **Bob te rappellera exactement quand capturer à la fin de chaque tâche concernée.**
> Voici le guide complet pour référence.

### Comment faire une capture correcte

1. **Agrandir la fenêtre de chat Bob** — clique sur l'icône d'agrandissement pour avoir la réponse en plein écran
2. **Faire défiler jusqu'au début** de la réponse importante à capturer
3. **Vérifier qu'aucune valeur sensible n'est visible** (clé API, token, mot de passe) — si oui, floute avec un outil comme Paint ou Greenshot avant de sauvegarder
4. **Capturer** avec `Win + Shift + S` (Windows) ou `Cmd + Shift + 4` (Mac)
5. **Nommer le fichier exactement** comme indiqué ci-dessous
6. **Déposer dans `bob_sessions/`** à la racine du projet

### Calendrier des captures

| Capture | Déclenché après | Nom exact du fichier | Ce qu'on doit voir |
|---|---|---|---|
| 📸 **Capture 1** | Fin Tâche 1 (après `/init`) | `01_init_repository_scan.png` | Bob analysant l'arborescence du repo, listant les fichiers créés |
| 📸 **Capture 2** | Fin Tâche 2 | `02_connectors_generation.png` | Bob écrivant osv_client.py et electricity_client.py |
| 📸 **Capture 3** | Fin Tâche 3 ou 4 | `03_core_metrics_refactoring.png` | Bob en mode plan/agent générant SCI/SPSC ou un sous-agent en action |
| 📸 **Capture 4** | Fin Tâche 7 | `04_tests_and_summary.png` | Le Task Session Summary de Bob après génération des tests |

### Export Markdown (bonus)
Si ton extension Bob propose "Export session" ou "Copy as Markdown" :
- Clique sur `...` ou l'icône d'export dans le panneau Bob
- Enregistre sous `bob_sessions/session_<nom_tache>.md`
- Exemple : `bob_sessions/session_connectors.md`

---

## Tâche 1 — Setup environnement et structure du projet

**Intent :** Poser les fondations sécurisées du projet : règles Bob, fichiers d'exclusion, arborescence complète, fichiers d'init Python, et configuration des variables d'environnement. C'est le prérequis bloquant pour toutes les autres tâches.

**Expected Outcomes :**
- Dossier `.bob/` créé avec `rules.md` définissant les règles de gouvernance
- `.gitignore` et `.bobignore` protégeant contre toute fuite de secrets
- Arborescence complète créée : `backend/`, `connectors/`, `core/`, `frontend/`, `tests/`, `docs/`, `bob_sessions/`
- Fichiers `__init__.py` présents dans chaque module Python
- `.env.example` documentant toutes les variables nécessaires sans valeurs réelles
- `requirements.txt` listant toutes les dépendances du projet
- `docs/architecture.md` initialisé avec le modèle de base
- `README.md` initialisé

**Todo List :**
- [ ] Créer `.bob/rules.md` avec les règles de workflow, sécurité et documentation
- [ ] Créer `.gitignore` (exclure .env, venv/, __pycache__/, *.key, *.log, node_modules/)
- [ ] Créer `.bobignore` (exclure venv/, node_modules/, *.log, bob_sessions/)
- [ ] Créer les dossiers : backend/, connectors/, core/, frontend/, tests/, docs/, bob_sessions/
- [ ] Créer `bob_sessions/README.md` expliquant le contenu attendu et les noms de fichiers requis
- [ ] Créer les fichiers `__init__.py` vides dans backend/, connectors/, core/, tests/
- [ ] Créer `.env.example` avec les variables : ELECTRICITY_MAPS_API_KEY, OSV_API_URL, APP_ENV, PORT
- [ ] Créer `requirements.txt` avec : fastapi, uvicorn, httpx, streamlit, pytest, pytest-asyncio, pytest-cov
- [ ] Créer `docs/architecture.md` avec le modèle de base
- [ ] Créer `README.md` avec titre, description et instructions de démarrage minimales
- [ ] Créer `backend/config.py` pour la gestion des variables d'environnement via python-dotenv

**Relevant Context :**
- Fichier de référence : `BOB_KNOWLEDGE_BASE.md` section 1 (règles sécurité) et section 4 (architecture)
- Fichier de référence : `Idea.md` section 2 (structure répertoires)
- Règle critique : `.env` DOIT être dans `.gitignore` ET `.bobignore` — IBM surveille les repos GitHub

> 📸 **RAPPEL CAPTURE — après cette tâche :**
> Lance `/init` dans Bob, puis capture sa réponse complète montrant l'analyse de l'arborescence.
> **Nom du fichier :** `bob_sessions/01_init_repository_scan.png`
> **Comment :** `Win + Shift + S` → sélectionne le panneau Bob → enregistre dans `bob_sessions/`

**Status :** [ ] pending

---

## Tâche 2 — Connecteurs API (connectors/)

**Intent :** Implémenter les deux clients HTTP asynchrones qui alimentent le système en données réelles (vulnérabilités et intensité carbone). Chaque client doit avoir un fallback mock robuste pour garantir le fonctionnement en mode offline ou sans clé API.

**Sous-agent délégué : Agent Connectors**
> Contexte à fournir au sous-agent : schémas OSV.dev et ElectricityMaps de `BOB_KNOWLEDGE_BASE.md` sections 2A et 2B uniquement.

**Expected Outcomes :**
- `connectors/osv_client.py` : client asynchrone POST vers `https://api.osv.dev/v1/query`, parse `requirements.txt`, retourne les vulnérabilités avec CVSS. Fallback mock : jinja2==2.11.2 avec CVSS 7.5
- `connectors/electricity_client.py` : client asynchrone GET vers ElectricityMaps, retourne `carbonIntensity` en gCO2e/kWh. Fallback mock : `{"zone": "US-NY", "carbonIntensity": 210, "isMock": true}`
- Les deux fichiers ont des docstrings complètes et des type hints sur toutes les fonctions

**Todo List :**
- [ ] Déléguer à l'Agent Connectors avec le contexte des schémas API
- [ ] Implémenter `connectors/osv_client.py` avec `async def check_package(name, version, ecosystem) -> dict`
- [ ] Implémenter `connectors/osv_client.py` avec `async def scan_requirements(path) -> list[dict]`
- [ ] Ajouter le fallback mock OSV (jinja2 CVSS 7.5, fixed 2.11.3) si la requête échoue
- [ ] Implémenter `connectors/electricity_client.py` avec `async def get_carbon_intensity(zone) -> dict`
- [ ] Ajouter le fallback mock ElectricityMaps si le token est absent ou la requête échoue
- [ ] Vérifier que les clés API sont lues depuis les variables d'environnement uniquement (via config.py)

**Relevant Context :**
- Schéma OSV.dev : `BOB_KNOWLEDGE_BASE.md` section 2A
- Schéma ElectricityMaps : `BOB_KNOWLEDGE_BASE.md` section 2B
- Endpoint OSV : `POST https://api.osv.dev/v1/query`
- Endpoint ElectricityMaps : `GET https://api.electricitymap.org/v3/carbon-intensity/latest?zone=US-NY`
- Header ElectricityMaps : `auth-token: <API_KEY>`

> 📸 **RAPPEL CAPTURE — après cette tâche :**
> Capture l'échange complet où Bob (ou le sous-agent) a planifié et écrit les deux fichiers connecteurs.
> **Nom du fichier :** `bob_sessions/02_connectors_generation.png`
> **Comment :** Fais défiler jusqu'au moment où Bob affiche le code de `osv_client.py`, capture, puis répète pour `electricity_client.py`. Vérifie qu'aucune vraie clé API n'est visible.

**Status :** [ ] pending

---

## Tâche 3 — Moteurs mathématiques (core/metrics.py)

**Intent :** Implémenter les deux formules mathématiques fondamentales du projet. Ce module est le cœur intellectuel d'EcoSecOps — il quantifie l'empreinte carbone (SCI) et priorise les remédiations (SPSC). Il doit être pur, testé et précis.

**Sous-agent délégué : Agent Math Engine**
> Contexte à fournir au sous-agent : formules SCI et SPSC de `BOB_KNOWLEDGE_BASE.md` sections 3A et 3B uniquement.

**Expected Outcomes :**
- `core/metrics.py` : fonction `calculate_sci(energy_kwh, carbon_intensity, embodied_carbon, functional_unit) -> float` implémentant SCI = ((E * I) + M) / R
- `core/metrics.py` : fonction `calculate_spsc(cvss, current_intensity, reference_intensity, cpu_utilization) -> float` implémentant SPSC = α·CVSS + β·(I_actuel/I_ref) + γ·U_CPU avec α=0.5, β=0.3, γ=0.2
- Les fonctions ont des docstrings avec les références ISO/IEC 21031:2024
- Les valeurs par défaut documentées : M=0.05 gCO2e, I_ref=300 gCO2e/kWh

**Todo List :**
- [ ] Déléguer à l'Agent Math Engine avec les formules mathématiques en contexte
- [ ] Implémenter `calculate_sci()` avec les paramètres E, I, M (défaut 0.05), R (défaut 1)
- [ ] Implémenter `calculate_spsc()` avec CVSS, I_actuel, I_ref (défaut 300), U_CPU
- [ ] Ajouter les constantes α=0.5, β=0.3, γ=0.2 comme constantes de module documentées
- [ ] Ajouter les docstrings avec les formules mathématiques et les unités de chaque paramètre
- [ ] Ajouter des guards contre la division par zéro dans calculate_sci (R != 0)

**Relevant Context :**
- Formules : `BOB_KNOWLEDGE_BASE.md` section 3A et 3B
- Formule SCI : `Idea.md` section 3A
- Formule SPSC : `Idea.md` section 3B
- Standard de référence : ISO/IEC 21031:2024

> 📸 **RAPPEL CAPTURE — après cette tâche :**
> Capture Bob en mode plan ou agent au moment où il génère les algorithmes SCI/SPSC, idéalement avec le sous-agent visible dans l'interface.
> **Nom du fichier :** `bob_sessions/03_core_metrics_refactoring.png`
> **Comment :** Capture le moment où Bob affiche les formules implémentées dans le code. Si un sous-agent est visible dans l'interface, inclus-le dans la capture — c'est un excellent argument pour le critère "Utilisation avancée de Bob".

**Status :** [ ] pending

---

## Tâche 4 — Moteur de remédiation (core/remediator.py)

**Intent :** Implémenter le moteur qui applique automatiquement les correctifs de sécurité sur `requirements.txt` (mise à jour des versions vulnérables) et génère des suggestions de refactoring pour réduire l'empreinte carbone du code.

**Sous-agent délégué : Agent Remediator**
> Contexte à fournir au sous-agent : logique de patch requirements + structure de données retournée par osv_client.py.

**Expected Outcomes :**
- `core/remediator.py` : fonction `patch_requirements(requirements_path, vulnerabilities) -> dict` qui met à jour les versions vulnérables vers les versions fixées
- `core/remediator.py` : fonction `suggest_optimizations(sci_score) -> list[str]` qui retourne des recommandations textuelles de réduction carbone selon le score SCI
- Un fichier `requirements.txt` de test patché correctement (versions vulnérables remplacées)

**Todo List :**
- [ ] Déléguer à l'Agent Remediator avec la structure de données OSV en contexte
- [ ] Implémenter `patch_requirements()` : lire requirements.txt, identifier les packages vulnérables, remplacer les versions, écrire le fichier modifié
- [ ] Implémenter `suggest_optimizations()` : retourner des recommandations selon des seuils de SCI (faible/moyen/élevé)
- [ ] Ajouter une fonction helper `parse_requirements(path) -> list[dict]`
- [ ] Documenter chaque fonction avec docstrings et type hints

**Relevant Context :**
- Logique de remédiation : `BOB_KNOWLEDGE_BASE.md` section Step 5
- Les versions fixées viennent des données OSV retournées par osv_client.py (champ `fixed`)
- Format requirements.txt : `package==version` par ligne

**Status :** [ ] pending

---

## Tâche 5 — Backend FastAPI (backend/main.py)

**Intent :** Exposer les fonctionnalités du système via une API REST claire et documentée. Le backend orchestre les connecteurs et les moteurs core pour produire des réponses d'audit et de remédiation consommables par le frontend et par des outils tiers.

**Expected Outcomes :**
- `backend/main.py` : application FastAPI avec 3 endpoints opérationnels
- `GET /health` → retourne `{"status": "ok"}`
- `POST /api/audit` → accepte un chemin de requirements.txt, retourne vulnérabilités, SCI, SPSC pour chaque package
- `POST /api/remediate` → applique les patches et retourne le diff
- Documentation Swagger auto-générée accessible sur `/docs`
- Toutes les clés API chargées via `backend/config.py` depuis les variables d'environnement

**Todo List :**
- [ ] Créer `backend/main.py` avec l'instance FastAPI et les métadonnées (titre, version, description)
- [ ] Implémenter `GET /health`
- [ ] Définir les modèles Pydantic pour les requêtes et réponses de `/api/audit`
- [ ] Implémenter `POST /api/audit` en orchestrant osv_client, electricity_client, calculate_sci, calculate_spsc
- [ ] Définir les modèles Pydantic pour `/api/remediate`
- [ ] Implémenter `POST /api/remediate` en appelant patch_requirements
- [ ] Vérifier que le serveur démarre avec `uvicorn backend.main:app`

**Relevant Context :**
- Endpoints définis : `BOB_KNOWLEDGE_BASE.md` section Step 6 et `Idea.md` section Step 6
- config.py créé en Tâche 1
- Connecteurs créés en Tâche 2, moteurs créés en Tâches 3 et 4

**Status :** [ ] pending

---

## Tâche 6 — Dashboard Streamlit (frontend/app.py)

**Intent :** Construire l'interface utilisateur interactive qui rend le projet démo-able et compréhensible par le jury. Le dashboard doit afficher en temps réel les scores SCI, les CVEs détectées, l'intensité carbone, et permettre de déclencher la remédiation en un clic.

**Expected Outcomes :**
- `frontend/app.py` : dashboard Streamlit fonctionnel
- Section d'upload ou saisie du chemin vers requirements.txt
- Affichage du score SCI avec jauge visuelle
- Tableau des vulnérabilités CVE avec score CVSS et version fixée
- Affichage de l'intensité carbone en temps réel (avec badge "MOCK" si fallback)
- Bouton "Exécuter la remédiation" déclenchant l'appel à `/api/remediate`
- Affichage du diff des fichiers patchés

**Todo List :**
- [ ] Créer `frontend/app.py` avec la configuration Streamlit (titre, layout wide, favicon)
- [ ] Implémenter la section d'input (upload requirements.txt ou chemin manuel)
- [ ] Implémenter l'appel à `/api/audit` et l'affichage des résultats
- [ ] Créer la jauge SCI avec `st.metric` et indicateurs de tendance
- [ ] Créer le tableau CVE avec colonnes : Package, Version, CVSS, Sévérité, Version Fixée
- [ ] Afficher l'intensité carbone avec badge "MOCK" conditionnel
- [ ] Implémenter le bouton de remédiation et l'affichage du diff

**Relevant Context :**
- UI décrite dans `Idea.md` section Step 7
- Le frontend appelle le backend FastAPI (port par défaut 8000)
- L'URL du backend doit être configurable via variable d'environnement

**Status :** [ ] pending

---

## Tâche 7 — Tests Pytest (tests/)

**Intent :** Garantir la fiabilité du code et atteindre l'objectif de >80% de couverture requis par le hackathon. Les tests valident les connecteurs (avec mocks HTTP), les formules mathématiques, et le moteur de remédiation.

**Sous-agent délégué : Agent Tests**
> Contexte à fournir au sous-agent : signatures des fonctions testées + valeurs de référence OSV et ElectricityMaps mock.

**Expected Outcomes :**
- `tests/test_connectors.py` : tests unitaires pour osv_client et electricity_client avec mocks httpx
- `tests/test_metrics.py` : tests unitaires pour calculate_sci et calculate_spsc avec valeurs connues
- Couverture de code >80% vérifiable avec `pytest --cov`
- Tous les tests passent en mode offline (pas de vrais appels API dans les tests)

**Todo List :**
- [ ] Déléguer à l'Agent Tests avec les signatures de fonctions et valeurs mock en contexte
- [ ] Implémenter les tests de `osv_client.check_package()` avec mock httpx (succès + échec + fallback)
- [ ] Implémenter les tests de `electricity_client.get_carbon_intensity()` avec mock httpx (succès + fallback)
- [ ] Implémenter les tests de `calculate_sci()` avec des valeurs de référence connues
- [ ] Implémenter les tests de `calculate_spsc()` avec les poids α=0.5, β=0.3, γ=0.2
- [ ] Implémenter les tests de `patch_requirements()` avec un fichier requirements.txt de test
- [ ] Lancer `pytest --cov=. --cov-report=term-missing` et vérifier >80%

**Relevant Context :**
- Valeur de test OSV : jinja2==2.11.2, CVSS=7.5, fixed=2.11.3
- Valeur de test ElectricityMaps mock : carbonIntensity=210
- Formules vérifiables manuellement avec des entrées simples

> 📸 **RAPPEL CAPTURE — après cette tâche :**
> Capture le Task Session Summary affiché par Bob une fois les tests générés et validés.
> **Nom du fichier :** `bob_sessions/04_tests_and_summary.png`
> **Comment :** A la fin de la session, Bob affiche un résumé. Capture ce panneau en entier. Si Bob propose un export Markdown, clique dessus et enregistre sous `bob_sessions/session_tests.md`.

**Status :** [ ] pending

---

## Tâche 8 — README et polish final

**Intent :** Finaliser la documentation pour la soumission au hackathon. Le README est le premier élément que le jury voit — il doit être clair, complet et convaincant.

**Sous-agent délégué : Agent Docs**
> Contexte à fournir au sous-agent : critères d'évaluation du hackathon + architecture finale du projet.

**Expected Outcomes :**
- `README.md` complet : description du projet, architecture, installation, utilisation, APIs, formules SCI/SPSC
- `docs/architecture.md` : diagramme d'architecture textuel et description des choix techniques
- `.env.example` à jour avec toutes les variables
- Problem statement et usage statement rédigés (<500 mots chacun)

**Todo List :**
- [ ] Déléguer à l'Agent Docs avec les critères d'évaluation et l'architecture en contexte
- [ ] Compléter `README.md` avec badges, description, prérequis, installation, commandes de démarrage
- [ ] Documenter les endpoints API dans le README
- [ ] Documenter les formules SCI et SPSC dans le README avec les unités
- [ ] Compléter `docs/architecture.md` avec les choix techniques justifiés
- [ ] Rédiger le problem statement (<500 mots)
- [ ] Rédiger l'usage statement (<500 mots)
- [ ] Vérifier que `.env.example` liste toutes les variables utilisées dans le code

**Relevant Context :**
- Livrables requis : `BOB_KNOWLEDGE_BASE.md` section 1
- Critères d'évaluation : 25% qualité/présentation

**Status :** [ ] pending

---

## Tâche 9 — Commits des captures de session IBM Bob (bob_sessions/)

**Intent :** Constituer et commiter les preuves obligatoires d'utilisation d'IBM Bob 2.0 pour la soumission au hackathon. Cette tâche est la consolidation finale des captures effectuées tout au long du projet.

**Expected Outcomes :**
- 4 captures d'écran présentes dans `bob_sessions/` avec les noms exacts requis
- Exports Markdown des sessions Bob si disponibles
- Aucune clé API, token ou secret visible sur les captures
- Commit Git dédié avec le message conventionnel requis

**Todo List :**
- [ ] Vérifier que les 4 captures sont présentes dans `bob_sessions/` avec les bons noms
- [ ] Vérifier sur chaque capture qu'aucune clé API (IBM Cloud, ElectricityMaps) n'est visible
- [ ] Flouter ou masquer toute valeur sensible avant commit
- [ ] Ajouter les exports Markdown si disponibles (`bob_sessions/session_*.md`)
- [ ] Exécuter : `git add bob_sessions/`
- [ ] Exécuter : `git commit -m "docs: add IBM Bob session summary screenshots"`
- [ ] Exécuter : `git push origin main`

**Relevant Context :**
- Exigences officielles de soumission hackathon (lablab.ai)
- Les captures sont réalisées au fil des tâches 1, 2, 3 et 7 — voir les rappels dans chaque tâche
- Ne pas attendre la fin pour commencer à capturer — chaque capture doit être faite à chaud

**Status :** [ ] pending

---

## Ordre d'exécution recommandé

```
Tâche 1 (Setup)
    ↓ [📸 Capture 1 après /init]
Tâche 2 (Connectors) ← Agent Connectors
    ↓ [📸 Capture 2]
Tâche 3 (Metrics) ← Agent Math Engine    +    Tâche 4 (Remediator) ← Agent Remediator
    ↓ [📸 Capture 3]
Tâche 5 (Backend FastAPI)
    ↓
Tâche 6 (Frontend Streamlit)
    ↓
Tâche 7 (Tests) ← Agent Tests
    ↓ [📸 Capture 4]
Tâche 8 (README) ← Agent Docs
    ↓
Tâche 9 (Commit captures bob_sessions/)
```

**Règles d'exécution :**
- Chaque tâche de code = une session Bob (principe "Une tâche, une session")
- Les tâches 3 et 4 peuvent être parallélisées via deux sous-agents simultanés
- Les captures sont faites **à chaud**, jamais reconstituées après coup
- Bob rappellera le moment de chaque capture à la fin de la tâche concernée
