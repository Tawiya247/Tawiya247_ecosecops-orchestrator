# bob_sessions/ — Captures de Session IBM Bob 2.0

Ce dossier contient les preuves obligatoires d'utilisation d'IBM Bob 2.0 pour la soumission au Hackathon IBM Bob 2.0 (lablab.ai).

## Fichiers attendus

| Fichier | Déclenché après | Ce qu'on doit voir |
|---|---|---|
| `01_init_repository_scan.png` | Fin Tâche 1 (après `/init`) | Bob analysant l'arborescence du repo, listant les fichiers créés |
| `02_connectors_generation.png` | Fin Tâche 2 | Bob écrivant `osv_client.py` et `electricity_client.py` |
| `03_core_metrics_refactoring.png` | Fin Tâche 3 ou 4 | Bob en mode plan/agent générant SCI/SPSC ou un sous-agent en action |
| `04_tests_and_summary.png` | Fin Tâche 7 | Le Task Session Summary de Bob après génération des tests |

## Optionnel — Exports Markdown

Si l'extension Bob propose "Export session" ou "Copy as Markdown" :
- Enregistrer sous `bob_sessions/session_<nom_tache>.md`
- Exemples : `session_connectors.md`, `session_tests.md`

## Règles de sécurité

> ⚠️ **CRITIQUE** : Aucune clé API, token ou mot de passe ne doit être visible sur les captures.
> Flouter toute valeur sensible avec Paint, Greenshot ou équivalent **avant** de commiter.

## Comment capturer (Windows)

1. Agrandir la fenêtre de chat Bob (icône d'agrandissement)
2. Faire défiler jusqu'au début de la réponse à capturer
3. Vérifier l'absence de secrets visibles
4. `Win + Shift + S` → sélectionner la zone → enregistrer avec le nom exact requis
5. Placer le fichier dans ce dossier `bob_sessions/`

## Commit final (Tâche 9)

```bash
git add bob_sessions/
git commit -m "docs: add IBM Bob session summary screenshots"
git push origin main
```
