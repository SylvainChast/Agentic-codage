# Exploitation, CI et intégration

## Installation et mises à jour

Installer une version connue du framework dans un environnement virtuel. Conserver sa version
avec la configuration du projet. Pour un produit, éviter une dépendance sur une branche flottante :
utiliser un tag ou commit examiné. Le paquet inclut les schémas et les assets nécessaires à `init`
et `map`. Aucun processus d’arrière-plan ni clé API ne sont requis.

## Worktrees et réservations

Un clone Git, des worktrees par mission, un coordinateur qui attribue les contrats. La base SQLite
est dans `<git-common-dir>/agentic-codage/leases.sqlite3`. Elle n’est ni publiée ni transportée par Git.
`framework lease list` donne l’état vivant ; le HTML n’essaie pas de présenter ces baux comme une
information durable. Les baux expirent ; ne jamais continuer à écrire après expiration sans renouveler.

Après un crash, reprendre depuis la tâche et le dernier run. Un acteur du même nom peut renouveler
son bail ; les noms ne sont pas authentifiés. Éviter les identités partagées entre sessions. Ne pas
synchroniser le fichier SQLite par Dropbox, NFS ou un partage réseau.

## CI de ce dépôt

`.github/workflows/ci.yml` exécute les tests, les validations, les adaptateurs et une génération de
carte sur Linux, macOS et Windows avec Python 3.11 et 3.13. Les actions sont épinglées par commit,
les permissions limitées à la lecture et aucun secret n’est nécessaire. La carte créée en CI est
un résultat du run ; la version committée peut être régénérée localement avec `framework map`.

Cette CI vérifie le framework ; un produit doit ajouter ses propres tests, scans et contrôles
opérationnels. La CI normale n’impose pas un contrat de mission pour une PR de cadrage. Pour une
PR d’implémentation, le workflow `scope.yml` lit la ligne `Task: T-…` du corps de la PR et compare le diff au SHA de base
fourni par GitHub. Une PR de cadrage porte `Type: planning` et ne peut modifier que des contrats
planifiés, décisions, findings et documents. Un lancement manuel reste possible pour diagnostiquer
un contrat/base explicites. Le propriétaire doit rendre le job `scope` obligatoire sur la branche.

Ne pas faire confiance à un simple statut écrit par un agent. Pour une réelle porte d’intégration,
utiliser des workflows contrôlés et des paramètres de base issus de la plateforme, pas un SHA choisi
librement par l’auteur. Ne pas employer `pull_request_target` avec du code non fiable et des secrets.

## Protection GitHub à configurer

Dans les règles de la branche de livraison :

1. Exiger une pull request et les contrôles CI pertinents.
2. Exiger une revue distincte ; invalider les approbations périmées lorsque le diff change.
3. Protéger les règles, workflows et fichiers sensibles par revue des propriétaires (`CODEOWNERS`).
4. Tester les changements sur la branche cible à jour, ou utiliser la file de fusion disponible.
5. Restreindre les contournements et les jetons capables d’écrire/publier.

Les fonctionnalités et conditions de disponibilité varient selon le dépôt et l’offre GitHub.
[Documentation des branches protégées](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).
Ces réglages ne sont pas créés automatiquement par `framework init`.

## Commandes de vérification

Lire les tableaux `argv` de la politique avant exécution. Ils tournent dans la racine du projet avec
les permissions du processus appelant. Le délai est par commande. Sur POSIX, le groupe de processus
est tué au dépassement ; sous Windows, le processus direct est tué, et un runner isolé doit gérer les
descendants éventuels. Les logs conservés sont limités à environ 1 Mio après exécution ; le volume
sur disque pendant l’exécution n’est pas plafonné. Le code non fiable exige un environnement isolé.

## Sauvegarde et restauration

La mémoire durable est restaurable depuis Git. Préserver les logs référencés ; les supprimer fait
échouer la validation des preuves. Une réservation perdue peut être réacquise après vérification du
travail en cours ; sa base n’est pas un historique à auditer. Ne pas restaurer aveuglément un bail
périmé. La v0.1 ne déploie aucune base de produit et ne gère pas ses sauvegardes.
