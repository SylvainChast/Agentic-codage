# Utiliser Agentic Codage dans ce projet

Ce projet embarque les instructions partagées dans `.framework/OPERATING.md` et ses réglages
dans `.framework/policy.json`. Les fiches sont en JSON, une par entité. `framework schema KIND`
affiche le contrat des données. La documentation complète accompagne le dépôt du framework :
https://github.com/SylvainChast/Agentic-codage/tree/main/docs

## Démarrage

Installer le framework avec Python 3.11+, configurer de vrais tests dans `policy.json`, puis
committer les instructions et la configuration. L’initialisation fournit un contrôle volontairement
en échec. Les règles d’éditeur sont des instructions. Le contrôleur optionnel `orchestration` lance des modèles
via des CLI configurées ; il n’accorde pas de permissions supplémentaires.

## Commandes

`framework task create --help` : déclarer titre, propriétaire, chemins, critères, livrables et budget.
`framework lease acquire TASK --owner ACTOR` : réserver chemins et ressources pendant une heure.
`framework task start TASK --actor ACTOR` : vérifier dépendances, réservation et budget enregistré.
Implémenter dans un worktree dédié. Renouveler le bail avant son expiration.
`framework run record --help` : journal et coût de chaque exécution, même ratée.
`framework verify TASK` : exécuter les vrais contrôles et conserver une preuve.
`framework task submit TASK --actor ACTOR` : transmettre à la revue.
`framework review record --help` : revue indépendante, sur tous les critères exacts et une preuve actuelle.
`framework task accept TASK --review REVIEW --actor ACTOR` : accepter le livrable, sans merge/déploiement.
`framework lease release TASK --owner ACTOR` : libérer une réservation.
`framework map` : générer `docs/carte-du-code.html`, lisible hors ligne.
`framework context CHEMIN` : contexte ciblé pour le prochain agent.
`framework costs` : coûts par tâche et par livrable accepté.
`framework check --base COMMIT --task TASK` : vérifier le périmètre contre un contrat préalablement enregistré.

## Coûts

Une devise à deux décimales ; les montants sont en centimes entiers. Chaque run inclut coût LLM,
infrastructure et temps humain valorisé. Utiliser `actual` pour les coûts observés, `estimate` avec
une méthode expliquée, ou `unknown` sans montant. Les coûts inconnus rendent les ratios incomplets.
Les coûts globaux par livrable accepté incluent les échecs et les tâches abandonnées. Une tâche
acceptée compte tous ses livrables : découper les acceptations partielles en tâches distinctes.

## Frontières

Les identités sont déclarées et les preuves sont locales. Une branche protégée et une CI contrôlée
par le propriétaire sont nécessaires contre la falsification. Les baux coordonnent seulement les
worktrees d’un clone sur un disque local ; plusieurs clones nécessitent un coordinateur externe.
Un bail ne bloque pas un éditeur qui l’ignore. Le budget limite les démarrages via la CLI, pas une
API LLM externe. Les commandes de vérification exécutent du code avec vos permissions : les lancer
dans un environnement isolé pour les contributions non fiables. Ne jamais consigner de secrets.

## Orchestration optionnelle (0.2)

L’utilisateur choisit chaque modèle. `framework orchestration init --adapter codex --model ID`
configure les quatre rôles ; `set-role orchestrator --adapter claude --model ID` en change un seul.
Les autres rôles sont worker, reviewer et arbiter. Un pont `--adapter command --command-json
'["/chemin/executable"]'` permet d’ajouter un fournisseur, avec un contrat JSON stdin/stdout.
`doctor` vérifie les exécutables sans appel payant. Lire `orchestration --help` et le skill
`swarm-orchestrate` pour les commandes. Les identifiants ne sont jamais remplacés automatiquement.

Committer code, politique, profil et contrat avant `orchestration run TASK`. Le contrôleur crée des
worktrees, délègue selon les dépendances, vérifie et fait relire. Chaque appel est comptabilisé.
Une session ready attend `orchestration integrate SESSION --actor ACTOR`, qui applique le candidat
et enregistre l’acceptation sans commit ni push. `cancel SESSION` demande l’arrêt ; `feedback SESSION
--message TEXTE` intervient au prochain plan. Une nouvelle exécution après blocage repart du code
committé, sans reprise implicite du candidat précédent. Les coûts historiques restent imputés.

Les worktrees ne sont pas une sandbox système. Le pont est du code de confiance ; les restrictions
natives dépendent de la CLI. Les budgets sont contrôlés avant appel sur les montants connus, pas
auprès du fournisseur. Les coûts absents restent inconnus. Les permissions, dépendances de test et
comptes doivent être configurés par l’opérateur. Le guide détaillé est dans le dépôt du framework :
https://github.com/SylvainChast/Agentic-codage/blob/main/docs/orchestration.md
