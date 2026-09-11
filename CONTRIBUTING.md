# Contribuer

Lire le README, `.framework/OPERATING.md`, l’architecture et les limites. Python 3.11+ et Git suffisent
pour les tests. Installer le paquet est facultatif pour modifier les sources.

Déclarer un contrat de tâche pour un changement significatif. Garder les modifications atomiques,
les erreurs compréhensibles et les dépendances d’exécution minimales. Pour une nouvelle règle,
montrer le cas qu’elle empêche et tester l’invariant ; éviter les tests qui ne font que recopier
l’implémentation. Ne pas désactiver une vérification pour faire passer une modification.

Commandes :

```bash
python3 -m unittest discover -s tests -v
python3 bin/framework check
python3 bin/framework adapters --check
python3 bin/framework map
python3 bin/framework map --check
```

Un changement de schéma doit expliquer la compatibilité et la migration des anciens projets.
Un changement d’asset doit régénérer et examiner les copies d’adaptateurs. Documenter toute nouvelle
commande dans `docs/cli.md` et les exemples. Les commits suivent `feat:`, `fix:`, `docs:`, `test:` ou
`chore:` ; les branches de contribution utilisent par défaut `codex/`.

Les PR expliquent le problème, le comportement obtenu, les tests exécutés et les limites restantes.
Les modifications aux politiques, workflows et règles nécessitent une revue distincte. Ne pas
inventer une revue indépendante pour accepter sa propre tâche. Les contributions et droits de
redistribution doivent être clarifiés par le propriétaire avant ouverture à des tiers.
