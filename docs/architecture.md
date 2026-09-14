# Architecture

## Principes retenus

1. Python 3.11+ et bibliothèque standard : une CLI invocable depuis n’importe quel outil.
2. JSON versionné, un fichier par entité ; génération déterministe d’une carte HTML autonome.
3. SQLite local dans le répertoire Git commun pour les réservations entre worktrees.
4. Vérifications exécutées et revues liées au contenu observé, sans confondre une déclaration
   locale avec une attestation signée par une infrastructure de confiance.
5. Sources d’adaptateurs uniques ; refus d’écraser une instruction existante.

## Modules

| Module | Responsabilité |
|---|---|
| `cli.py` | Arguments, dispatch, sorties JSON et codes de retour |
| `store.py` | Chemins, JSON strict, schémas, écritures atomiques, empreinte Git-visible |
| `bootstrap.py` | Initialisation non destructive et génération des adaptateurs |
| `lifecycle.py` | Création des contrats, transitions et enregistrement des runs |
| `leases.py` | Réservations SQLite atomiques, expiration, propriétaire et ressources |
| `evidence.py` | Exécution des commandes, délais, logs, revue et acceptation |
| `checks.py` | Cohérence entre fiches, cycles, exceptions, taille et périmètre du diff |
| `costs.py` | Calculs en unités mineures, complétude et ratios de livraison |
| `context.py` | Extraction des décisions, risques et journaux liés à un chemin |
| `map.py` | Instantané et rendu HTML, détection des données périmées |
| `orchestration/` | Profils, protocoles, transports, appels comptabilisés, worktrees et contrôleur |
| `method/` | Catalogue, gabarits, documents liés, revues de cadrage, contexte et préparation de PR |
| `assets/` | Schémas, instructions, skills et interface HTML autonome |

`store.py` fournit les primitives. Les modules métier les composent. La CLI ne contient pas les
règles de calcul. Le HTML consomme le même instantané que les commandes ; il n’introduit pas de
statuts ou de résultats calculés par un autre modèle.

## Mémoire durable

```text
.framework/
  policy.json
  orchestration.json             # facultatif, modèles choisis
  orchestrations/O-….json       # profils figés et journal de session
  OPERATING.md
  tasks/T-….json
  decisions/D-….json
  findings/F-….json
  exceptions/X-….json
  runs/R-….json
  evidence/E-….json
  evidence/E-…-0.log
  reviews/V-….json
  artifacts/A-….json            # documents de cadrage et entrées
  artifact_reviews/Q-….json    # revues de cadrage
  method/                      # procédures et gabarits générés
```

Les identifiants utilisent des UUID tronqués à 48 bits, sans compteur central ; la création exclusive
refuse une collision. Les écritures remplacent atomiquement un fichier complet après flush/fsync.
Les journaux et preuves sont créés exclusivement par la CLI ; l’historique Git rend les modifications
ultérieures examinables. Cela n’est pas un stockage immuable face à un utilisateur ayant les droits disque.

## Candidat vérifié

L’empreinte SHA-256 couvre les noms, contenus et bit exécutable des fichiers suivis par Git ainsi que
les fichiers non suivis et non ignorés. Les suppressions sont représentées. Les liens symboliques sont
empreintés comme liens, sans suivre leur cible ; les sous-modules ne sont pas pris en charge.

Sont exclus : les fiches de cycle de vie (tâches, runs, preuves, revues, findings, exceptions),
`.framework/local/` et le HTML généré. Les décisions, interfaces, documents de cadrage et la politique sont inclus. Les revues de cadrage sont des traces de cycle de vie exclues. Le contrat propre
à la tâche est empreinté séparément, hors statut et acceptation. Les fichiers ignorés, dépendances
installées et ressources externes ne sont pas attestés : verrouiller les dépendances et utiliser une
CI contrôlée pour la livraison. L’empreinte est volontairement globale : une modification indépendante
peut invalider une preuve. Cette prudence simplifie la v0.1.

## Coordination

`BEGIN IMMEDIATE` sérialise la lecture des réservations et leur acquisition. Les chemins recouvrants
et les ressources identiques sont exclus simultanément. Les réservations expirées sont purgées dans
la transaction. Le répertoire Git commun rapproche tous les worktrees du clone sans créer un fichier
central de conflits dans les PR. Le disque doit être local ; aucun support de SQLite sur partage réseau
n’est revendiqué.

Les réservations sont coopératives. Une seule session doit modifier une tâche donnée. Le framework
n’ajoute pas de verrou d’édition à l’IDE ni de service distribué. Les écritures de statut d’une même
tâche ne sont pas protégées par une comparaison de version : le coordinateur évite deux propriétaires
concurrents sous la même identité.

## Carte HTML

Le rendu lit les sources, valide les fiches et assemble une page autonome. Les sources HTML, CSS
et JavaScript sont séparées dans les assets pour rester lisibles ; le générateur les embarque dans
un seul HTML. La recherche et les filtres
fonctionnent côté navigateur. Les valeurs des agents sont insérées par `textContent` ; le JSON embarqué
échappe `<` pour empêcher une fermeture prématurée de balise script. Aucun contenu de fiche n’est
exécuté. Aucune requête réseau n’est nécessaire.

`map --check` compare les données, pas l’heure ni le commit observé. Ainsi un commit qui ne change pas
les données n’invalide pas le rendu. Il faut régénérer après une évolution du code ou des fiches. La carte
n’est pas une topologie AST complète ; `scope`, `paths` et les décisions matérialisent les relations.

## Moteur de délégation

`profiles` valide le choix utilisateur ; `protocol` valide les réponses et le graphe ; `adapters`
construit les appels natifs/génériques ; `transport` surveille délai, annulation et sorties ; `calls`
réserve les places et comptabilise ; `workspaces` isole et applique les patchs ; `engine` pilote les
tours, preuves, revues et intégration explicite. Voir [le guide](orchestration.md).

## Préparation avant délégation

`method.catalog` définit les parcours et procédures ; `templates` génère et valide les PRD/story ;
`artifacts` enregistre les révisions et les revues ; `workflow` vérifie leur fraîcheur et prépare
le contexte pertinent ; `shipping` produit un corps de PR local. Le moteur applique la condition
`require_ready` avant chaque appel et avant intégration ; la vérification la réévalue aussi.
Le contrat et le contexte figés doivent toujours correspondre au cadrage courant. Les documents
Markdown enregistrés sont protégés des écritures des travailleurs. Il conserve le contexte de cadrage
dans la session puis transmet les documents sélectionnés aux rôles concernés.

Les contrôles portent sur des références et des déclarations vérifiables localement. Ils ne
mesurent pas la justesse d’une exigence, l’authenticité d’une identité ou l’obéissance d’un modèle.
Les fichiers de cadrage appartiennent à la base approuvée ; une revue `Q-…` ne permet pas de
modifier le périmètre d’implémentation. Voir [la méthode](methodologie.md).
