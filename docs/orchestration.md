# Orchestration avec modèles choisis par l’utilisateur

La version 0.2 fournit un contrôleur local qui appelle les modèles, planifie une mission, distribue
les travaux, exécute les contrôles et sollicite une revue séparée. Le JSON reste la source versionnée ;
la vue **Orchestration** de la carte HTML montre les sessions, profils, appels et résultats.

## Choisir les responsabilités et les modèles

| Rôle | Responsabilité | Écriture produit |
|---|---|---|
| `orchestrator` | Décomposer le contrat en travaux bornés et dépendances | Non |
| `worker` | Implémenter un travail dans son worktree | Périmètre attribué |
| `reviewer` | Examiner le candidat, les preuves et tous les critères | Non |
| `arbiter` | Donner une orientation après échec des tests ou refus de revue | Non |

Un modèle capable de planification et de délégation est un choix utile pour une mission complexe.
Le framework **n’impose aucun modèle** : Astra, Fable, Sol, Opus ou tout autre modèle accessible dans
l’outil choisi. Ce sont des exemples de choix, pas une table de correspondance. Fournir l’identifiant
ou l’alias reconnu par votre CLI. Le framework ne traduit pas un nom commercial en identifiant.

```bash
framework orchestration init --adapter codex --model VOTRE_IDENTIFIANT
framework orchestration set-role orchestrator --adapter claude --model VOTRE_AUTRE_IDENTIFIANT
framework orchestration set-role worker --adapter codex --model VOTRE_MODELE_EXECUTANT
framework orchestration config
framework orchestration doctor
```

`init` attribue explicitement le même choix aux quatre rôles. `set-role` change seulement le rôle
nommé. Le modèle peut être identique pour plusieurs rôles : chaque appel reste une session neuve.
`doctor` vérifie les exécutables, sans connexion, achat, vérification de compte ni génération payante.
Si le binaire n’est pas dans PATH, utiliser `--command-json '["/chemin/vers/executable"]'`.

Le profil `.framework/orchestration.json` permet aussi de régler :

- `max_parallel` : travailleurs simultanés, défaut 2, maximum 16 ;
- `max_rounds` : cycles plan/travaux/tests/revue, défaut 2, maximum 20 ;
- `max_items` : taille maximale d’un plan, défaut 8, maximum 64 ;
- `timeout_seconds` : délai par appel, défaut 600, maximum 3600 ;
- `require_model_report` : refuser une réponse sans modèle déclaré, défaut false ;
- `accepted_models` par rôle : identifiants observés explicitement autorisés, incluant le choix demandé.

Un alias peut produire un identifiant de version différent. L’utilisateur peut l’autoriser avec
`set-role … --allow-observed IDENTIFIANT`. Il n’y a aucun repli automatique. Une déclaration ne
prouve pas cryptographiquement l’identité du fournisseur ; l’absence est marquée `unverified`,
un écart `mismatch` bloque la session. Le profil est figé dans chaque session pour l’audit.

## Exécuter et intégrer

Installer/configurer les CLI et leurs comptes avant tout lancement. Lire les tests de la politique,
enregistrer le contrat de tâche et prévoir les appels de coordination/revue dans `max_runs`.
Committer le code, la politique, le profil et le contrat. Les statuts et journaux peuvent rester non
committés. Le candidat conserve les octets du checkout propre, y compris lorsque Git convertit
les fins de ligne. Les projets avec liens symboliques dans les sources ne sont pas pris en charge
par le lancement automatique. Les worktrees ne recopient pas les dépendances ignorées ni les secrets du checkout :
préparer une vérification reproductible qui fonctionne dans un checkout neuf.

```bash
framework orchestration run T-IDENTIFIANT
framework orchestration show O-IDENTIFIANT
framework costs
framework map
# Après examen du candidat et dans le cadre de l’autorisation existante :
framework orchestration integrate O-IDENTIFIANT --actor votre-identite
framework map
```

`run` reste au premier plan. Il réserve le contrat et crée des worktrees détachés dans
`<git-common-dir>/agentic-codage/orchestration/O-…/`. Le plan est vérifié : identifiants uniques,
dépendances sans cycle, sous-périmètres du contrat. Les travaux prêts ayant des chemins disjoints
peuvent s’exécuter ensemble. Les périmètres recouvrants sont sérialisés. Les travailleurs suivants
partent du candidat intégrant leurs prédécesseurs. Des chemins disjoints ne garantissent pas une
indépendance sémantique : le plan et les tests doivent couvrir les interfaces communes.

Le contrôleur refuse les modifications hors périmètre, les changements de HEAD par le travailleur
et les nouveaux liens symboliques. Les instructions d’agents, `.framework`, `.github` et la carte
sont protégées des travailleurs automatiques ; leur évolution passe par le workflow manuel avec
revue. Les modifications des rôles de lecture sont détectées dans les fichiers Git-visibles.

Les commandes de la politique tournent réellement sur le candidat. Une réussite permet une revue
neuve, sans historique de conversation du travailleur. Le refus ou l’échec de vérification peut
solliciter l’arbitre puis un nouveau plan, dans la limite des tours et appels. Une erreur de transport,
un modèle inattendu, un conflit Git ou une sortie de périmètre bloque immédiatement. Les essais,
preuves échouées et coûts sont conservés. L’arbitre donne une orientation ; il ne tranche pas
entre deux branches concurrentes proposées comme alternatives.

`ready` signifie vérifié et approuvé dans un worktree, **pas livré dans votre checkout**.
`integrate` contrôle la fraîcheur du contrat, du code, des preuves et du candidat, applique le patch
au répertoire de travail puis enregistre l’acceptation. Il ne crée pas de commit sur votre branche,
ne pousse pas et ne déploie pas. Une modification du checkout impose une nouvelle session ; il
n’existe pas de rebase automatique des preuves. Les worktrees conservés sont inspectables avec
`git worktree list` et nettoyables explicitement avec `git worktree remove` après conservation des
artefacts utiles. Ne pas les supprimer avant intégration.

## Intervenir et reprendre

Depuis un autre terminal :

```bash
framework orchestration feedback O-IDENTIFIANT --message "Précision pour le prochain plan"
framework orchestration cancel O-IDENTIFIANT
```

Les messages sont lus au prochain tour de planification. Ils ne modifient pas le contrat ni un appel
en cours. L’annulation est coopérative, surveillée pendant les appels et avant chaque nouvel appel.
Une vérification produit en cours reste bornée par son délai propre. Une génération déjà facturée
n’est pas remboursée par l’arrêt du processus.

Une session bloquée ne reprend pas implicitement ses travaux partiels. Corriger la cause, committer
les changements nécessaires, puis lancer `run TASK` : nouveau plan, mêmes coûts historiques imputés
à la tâche. La reprise exacte d’un processus tué n’est pas implémentée. Après crash brutal, inspecter
les processus et le répertoire `TASK.lock` dans le stockage local avant de retirer un verrou devenu
orphelin ; ne jamais le retirer pour lancer deux contrôleurs sur la même tâche. Les baux expirent.

## Adaptateurs exécutables

**Codex** : `codex exec`, modèle explicite, session éphémère, configuration utilisateur ignorée,
schéma de sortie, événements JSONL, sandbox `read-only` ou `workspace-write`, approbations `never`.
Le coût reste inconnu faute de montant facturé ; les tokens observés sont conservés. Une réponse
sans identité de modèle reste non vérifiée. Voir [mode non interactif](https://developers.openai.com/codex/noninteractive).

**Claude Code** : impression JSON structurée, modèle explicite, session non persistée, outils de
lecture pour les rôles de lecture et Edit/Write pour le travailleur, sans Bash ni MCP additionnel.
Le montant `total_cost_usd` est utilisé uniquement dans un projet USD ; aucune conversion EUR n’est
inventée. Voir [référence CLI](https://code.claude.com/docs/en/cli-reference).

**Commande JSON** : pont explicite pour d’autres modèles/outils. Pas de shell implicite :

```bash
framework orchestration set-role orchestrator --adapter command --model modele-prive \
  --command-json '["{python}","/chemin/absolu/bridge.py"]'
```

Le pont reçoit sur stdin un objet avec `protocol_version: 1`, `role`, `model`, `payload`, `prompt`
et `response_schema`. Son cwd est le worktree. Il écrit exactement un objet JSON sur stdout :

```json
{"result":{"summary":"Résumé"},"model":"modele-prive","usage":{"currency":"EUR","cost_minor":12,"cost_source":"actual","input_tokens":300,"output_tokens":120}}
```

`result` doit suivre le schéma reçu : un plan contient `items`, une revue `verdict` et la liste exacte
`criteria`. `models` peut remplacer `model` pour rapporter plusieurs identités. Les coûts/tokens sont
facultatifs ; l’absence devient inconnue. La commande doit retourner un code nul, sans texte parasite
sur stdout ; stderr sert aux diagnostics. Les schémas se trouvent dans les assets du paquet.
Les entrées/sorties locales sont conservées sous `O-…/calls/`, hors Git ; elles peuvent contenir du
code privé. Chaque sortie est limitée à 4 MiB pendant la surveillance (un pic entre deux contrôles
reste possible). Les traces durables normalisées sont dans les runs et la session.

## Frontières de confiance et validation

Un worktree isole le candidat Git, **ce n’est pas une sandbox système**. Le pont générique est du
code de confiance disposant des droits du processus. Les restrictions natives dépendent des CLI.
Les contrôles de diff détectent des changements après l’appel ; ils ne protègent pas les secrets,
le réseau, les fichiers ignorés ou les autres répertoires. Utiliser une machine/conteneur dédié et
les permissions du fournisseur pour des agents non fiables. Sous Windows, l’arrêt garantit celui
du processus direct ; les descendants requièrent une isolation supplémentaire.

Le budget empêche de nouveaux appels selon les coûts déjà enregistrés et réserve les places
`max_runs` en vol. Il ne prédit pas le prix d’un appel, et deux appels parallèles peuvent dépasser
le montant restant. Configurer les limites fournisseur pour un plafond financier strict.
`costs` expose `by_role` et `by_orchestration`, avec coûts manquants et estimations. Les ratios par
livrable intègrent orchestration, arbitrage, revue et tentatives abandonnées.

La suite teste réellement processus, worktrees, contrôles et intégration avec un faux pont clairement
identifié. Les adaptateurs natifs sont testés sur construction des commandes et réponses représentatives ;
aucun compte Codex/Claude ni appel payant n’est validé de bout en bout par ces tests. Un refus natif
de permission bloque la session ; le framework n’ajoute pas de contournement automatique.
