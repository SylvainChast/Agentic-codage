---
status: implemented
phase: done
---

# Implémentation initiale

Le périmètre reprend la proposition acceptée : socle portable installable, contrats et réservations,
coûts par tâche/livrable accepté, vérifications et revue indépendante déclarée, HTML de référence,
adaptateurs pour les outils demandés, documentation et projet exemple.

## Phase unique de construction

- CLI Python 3.11+ sans dépendance d’exécution ; paquet installable et assets inclus.
- Contrats JSON, décisions, findings, exceptions, runs, preuves et revues.
- Réservations atomiques entre worktrees et contrôle de périmètre contre une base de confiance.
- Budgets, coûts connus/inconnus/estimés, ratios par tâche et livrable accepté.
- Vérifications liées au candidat, rejet des preuves obsolètes et des auto-revues déclarées.
- Carte HTML autonome, recherche et vues missions, décisions, risques, preuves, coûts et journaux.
- AGENTS, Claude, Cursor, Copilot, Gemini, Windsurf et skills de réalisation/revue.
- README, guides, modèle de données, architecture, qualité, exploitation et limites.
- Tests de régression, démonstration isolée et CI multi-OS.

## Critères de validation

Les tests couvrent le parcours complet et les échecs significatifs : coûts inconnus, tentatives ratées,
coûts humains, preuve obsolète, log altéré, timeout, auto-revue, collision de bail entre processus,
partage entre worktrees, cycles, exceptions expirées, sortie de périmètre et installation non destructive.
Le paquet doit s’installer dans un environnement vierge et y générer un projet et sa carte.
La démonstration doit exécuter de vrais tests métier et identifier explicitement ses coûts et revues simulés.

## Commandes

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_docs.py
python3 examples/demo.py
python3 bin/framework check
python3 bin/framework adapters --check
python3 bin/framework map
python3 bin/framework map --check
```

La CI distante et les sessions réelles dans chaque éditeur sont des validations distinctes.
Les preuves locales ne sont pas des attestations signées ; les limites sont documentées.

## Validation locale observée

47 tests de régression passent sur le Mac de construction. Le paquet a été installé dans un
environnement virtuel isolé et ses assets vérifiés hors du checkout. Les deux skills passent le
validateur de structure ; les liens de documentation sont valides. Le parcours de démonstration
exécute ses tests métier. La carte a été inspectée dans le navigateur : navigation, affichage des
coûts incomplets et recherche dans les décisions. Aucune session de modèle externe ni facturation
réelle n’a été simulée comme une mesure de production.
