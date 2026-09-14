# Méthode produit et développement

Cette méthode relie un besoin aux documents utiles, au code vérifié et à la préparation d'une PR.
Elle complète les réservations, interfaces, worktrees et coûts existants. Elle s'active par tâche ;
les anciennes tâches restent utilisables sans migration imposée. Elle est disponible dans la
version de travail, non encore publiée.

## Choisir le parcours

| Parcours | Usage | Documents requis avant exécution |
|---|---|---|
| `express` | Correction ou changement clair et borné | Plan court |
| `feature` | Fonctionnalité dans une application existante | Stories relues, conception locale, plan |
| `product` | Cadrage d'un produit ou changement transversal | PRD, architecture, stories relues, conception, plan |

`--ui` ajoute un design system requis, que l'on peut reprendre du produit existant. Utiliser ce
paramètre lorsqu'un système d'interface partagé est nécessaire ; une correction de texte n'exige
pas de recréer une bibliothèque de composants. La recherche reste ciblée sur une incertitude, sans
étape obligatoire ni recherche Internet systématique.

Le parcours est un choix explicite. L'orchestrateur ne change pas silencieusement de méthode ni
de modèle. Pour réviser ce choix, modifier le contrat de tâche dans une révision explicite ; les
preuves précédentes ne couvrent plus ce nouveau contrat.

## Commandes dans les agents

| Action | Claude / Cursor | Codex | Résultat |
|---|---|---|---|
| Recherche | `/research` | `$swarm-research` | Question résolue avec preuves et incertitudes |
| PRD | `/prd` | `$swarm-prd` | Exigences et exclusions |
| Architecture | `/architecture` | `$swarm-architecture` | Structure, données et interfaces |
| Design system | `/design-system` | `$swarm-design-system` | Conventions et composants UI |
| Stories | `/stories` | `$swarm-stories` | Résultats et critères testables |
| Revue des stories | `/story-review` | `$swarm-story-review` | Préparation approuvée ou blocages |
| Conception locale | `/design` | `$swarm-design` | Solution technique et UX |
| Plan | `/plan` | `$swarm-plan` | Travaux, dépendances et vérifications |
| Développement | `/execute` | `$swarm-execute` | Implémentation dans le périmètre |
| Revue du code | `/review` | `$swarm-review` | Conformité, qualité et verdict |
| Livraison Git | `/ship` | `$swarm-ship` | Préparation, puis PR si autorisée et outillée |

Exemple dans un agent qui expose les commandes :

```text
/prd T-IDENTIFIANT Définir le dashboard commercial avec les exigences connues de cette tâche.
/stories T-IDENTIFIANT
/story-review T-IDENTIFIANT
```

Le modèle actif de l'outil exécute la procédure. Ces fichiers ne créent pas une session payante
invisible et n'imposent aucun fournisseur. Une revue indépendante doit être exécutée par un
véritable acteur distinct des auteurs ; changer simplement son nom n'établit pas cette indépendance.

Selon la version de l'éditeur, certains noms comme `/plan` ou `/review` peuvent être réservés.
Sélectionner alors le skill du projet dans son interface ou utiliser la commande universelle :

```bash
framework method prompt prd --task T-IDENTIFIANT
```

Elle renvoie la procédure et un contexte structuré. Un agent qui sait lire et écrire des fichiers
peut la suivre, même si son éditeur ne prend pas en charge les slash commands. Sans outils, il peut
préparer un document et les commandes nécessaires, mais ne doit pas annoncer leur exécution.

## Installation et portabilité

`framework init` installe les points d'entrée. Dans un projet déjà initialisé, `framework adapters`
crée les fichiers manquants ; les conflits avec des instructions existantes sont signalés avant
écriture. Réconcilier les consignes au lieu de les écraser. `framework adapters --check` détecte
la dérive. Recharger le projet ou la liste de skills si l'éditeur ne voit pas les nouveaux fichiers.

Les procédures communes vivent dans `.framework/method/`. Les fichiers d'adaptation sont courts :

- `.agents/skills/swarm-*/SKILL.md` : skills portables, notamment Codex ;
- `.claude/skills/<étape>/SKILL.md` et `.cursor/skills/<étape>/SKILL.md` : commandes/skills ;
- `.github/prompts/<étape>.prompt.md` : fichiers de prompts pour VS Code Copilot ;
- `.gemini/commands/<étape>.toml` : commandes Gemini CLI ;
- `.windsurf/workflows/<étape>.md` : workflows Cascade.

Visual Studio et les autres hôtes disposent des consignes communes et de la CLI ; la découverte
native de prompts dépend de leur version. Les formats sont issus des documentations officielles,
mais cette livraison n'a pas été testée en session interactive dans chacun de ces éditeurs.

## Parcours technique, du cadrage à l'acceptation

Créer d'abord une tâche avec son périmètre (y compris les documents à écrire), ses critères, son
budget et son maximum d'exécutions. Le coût commence au cadrage, pas au premier fichier de code.

```bash
framework task create --title "Dashboard commercial" --owner pilote \
  --scope src/dashboard --scope tests/dashboard --scope docs/dashboard \
  --criterion "Les indicateurs respectent la période et les droits de l’utilisateur" \
  --deliverable "Dashboard commercial utilisable" --budget-minor 15000 --max-runs 20
framework method init T-IDENTIFIANT --track feature --ui
framework lease acquire T-IDENTIFIANT --owner pilote
framework task start T-IDENTIFIANT --actor pilote
framework method prompt stories --task T-IDENTIFIANT
```

Avant la revue, sélectionner la story et expliciter le contexte de l'agent :

```bash
framework method story T-IDENTIFIANT --id S-dashboard-periode --complexity 3 \
  --note "Réutiliser les contrôles de droits et le composant de période existants"
```

Après rédaction effective, enregistrer le document :

```bash
framework method record T-IDENTIFIANT --kind stories \
  --file docs/dashboard/stories.md --author redacteur
```

La réponse donne un identifiant `A-…`. Un relecteur distinct examine la story et ses entrées puis,
s'il n'y a pas de blocage, enregistre son verdict réel :

```bash
framework method review T-IDENTIFIANT --artifact A-STORIES \
  --reviewer relecteur --verdict approve --summary "Critères et dépendances cohérents après lecture"
```

Un refus utilise `request_changes` et un `--finding` par blocage. Zéro finding est une conclusion
valide. Un refus reste attaché à sa révision : corriger et enregistrer une nouvelle révision avant
une nouvelle approbation. La revue n'écrit pas elle-même les corrections.

Reprendre le design system existant :

```bash
framework method use T-IDENTIFIANT A-DESIGN-SYSTEM
```

Puis enregistrer la conception et le plan en déclarant leurs entrées :

```bash
framework method record T-IDENTIFIANT --kind design \
  --file docs/dashboard/design.md --author redacteur \
  --input A-STORIES --input A-DESIGN-SYSTEM
framework method record T-IDENTIFIANT --kind plan \
  --file docs/dashboard/plan.md --author redacteur \
  --input A-DESIGN --input A-STORIES
framework method status T-IDENTIFIANT
framework method gate T-IDENTIFIANT
```

Les identifiants de cet exemple sont à remplacer par les réponses réelles. `status` expose les
manques et problèmes sans exécuter les agents ; `gate` échoue si le cadrage n'est pas prêt.
En parcours Product, l'architecture référence le PRD, et les stories référencent le PRD et
l'architecture sélectionnés. La conception référence les stories et le design system si UI.
Le plan référence les stories et la conception, directement ou par leurs dépendances.

Avant orchestration, committer le contrat de tâche préparé, les documents, leurs fiches `A-…`,
les interfaces et la configuration. Les revues `Q-…` sont des traces de cycle de vie. Le moteur
refuse le lancement si la méthode n'est pas prête. Il recontrôle le contrat, les documents et
les revues avant chaque appel et avant intégration. Les travailleurs ne peuvent modifier aucun
Markdown enregistré comme document de cadrage, même si leur périmètre inclut sa documentation. En mode accompagné, l'agent appelle le même
contrôle avant de coder. `verify` et la validation d'une preuve courante vérifient également ce
prérequis : une écriture libre hors protocole ne produit pas une livraison acceptée par ces commandes.

## Révisions, réutilisation et contrôles

Chaque fiche `A-…` contient le chemin Markdown, son SHA-256, son auteur, la tâche de production
et les références avec empreintes de ses entrées. Un nouvel enregistrement sélectionne la nouvelle
révision de ce type pour la tâche. Une tâche sélectionne au plus une révision par type de document.
Les anciennes fiches restent historiques ; il est possible de garder plusieurs fichiers Markdown
versionnés pour que plusieurs tâches utilisent encore des versions différentes.

Le contrôleur détecte un document absent/modifié, un lien vers une ancienne révision sélectionnée,
un cycle ou une entrée incohérente. Les changements remontent aux documents dépendants. Une revue
`Q-…` est liée à la fiche et au cadrage de tâche ; modifier ses critères ou son périmètre l'invalide.

Les tâches peuvent partager le PRD, l'architecture et le design system via `method use`. Les coûts
de ces documents restent sur leur tâche de production. Les références ne les recopient pas dans
le coût de chaque feature. L'allocation analytique des coûts communs n'est pas automatisée.

Ces contrôles vérifient les relations déclarées et la fraîcheur. Ils ne prouvent pas qu'une story
est utile, qu'un document est complet ou qu'un agent a correctement compris un besoin. C'est le rôle
du cadrage et des revues effectives. Les identités locales ne sont pas authentifiées.

## Économie du contexte et des coûts

`method prompt` charge la procédure choisie et les documents pertinents pour cette étape. Le budget
par défaut des extraits est de 12 000 caractères, réglable avec `--max-chars`. Les documents restants
conservent leurs références et empreintes, avec `truncated: true` si un extrait est incomplet.
La limite concerne les extraits, pas la taille totale du prompt ni une mesure exacte des tokens.
Les critères et interfaces ne sont pas tronqués par ce mécanisme. Un agent doit lire les détails
manquants avant une décision qui en dépend.

Le contrôleur transmet ce contexte aux travailleurs avec la coordination existante. Il ne réécrit
pas le PRD à chaque appel. Une fois l'exécution lancée, la reconnaissance des interfaces et les
points de contrôle de lots restent obligatoires.

Comptabiliser chaque activité avec `run record --stage research|prd|architecture|design-system|stories|
story-review|design|plan|execute|review|ship`. Ce choix complète `purpose` et ne le remplace pas.
Les appels du contrôleur indiquent automatiquement plan, execute ou review ; ses checkpoints et
arbitrages appartiennent à l'exécution. Les procédures de cadrage exécutées dans l'hôte nécessitent
l'enregistrement par l'agent, car le framework ne voit pas la facturation de cette conversation.

`costs --task T-…` fournit `by_stage`, ainsi que les anciens runs sans étape dans `unstaged_runs`.
Les tentatives ratées comptent. Une facture inconnue reste inconnue. La préparation produit partagée
est visible sur sa propre tâche et au portefeuille.

## Préparer et publier une PR

Après implémentation, contrôles et revue indépendante, préparer le dossier local :

```bash
framework method ship T-IDENTIFIANT --base COMMIT_DU_CADRAGE --review V-REVUE
```

Cette commande vérifie le cadrage, la preuve, la revue et le périmètre par rapport à une base de
confiance qui contient le contrat préparé. Elle écrit une description de PR dans le stockage local
Git partagé du clone, sans ajouter de document au code vérifié. Elle ne crée pas la PR et ne déclare
pas la CI réussie. Le skill `/ship` explique à l'agent comment compléter cette description, committer
le changement, publier une PR brouillon via l'outil Git autorisé et observer la CI.

L'acceptation, l'intégration du candidat, la PR, la fusion et le déploiement sont des événements
séparés. Dans le contrôleur actuel, `orchestration integrate` applique et accepte le candidat avant
la préparation de PR : les coûts de shipping enregistrés ensuite sont donc postérieurs à cette
acceptation et visibles séparément. En mode accompagné, enregistrer le shipping avant acceptation
si l'unité économique souhaitée inclut cette étape. Le framework n'invente pas un déploiement ni
une deuxième acceptation pour masquer cette distinction.

## Validation et inspirations

Les tests portent sur les parcours, refus de préparation, dépendances périmées, identité déclarée
des relecteurs, contexte borné, coûts et préparation de PR. La démonstration
`python3 examples/method_demo.py` utilise un pont simulé avec de vrais worktrees, tests et contrôles.
Elle ne mesure pas la performance d'un modèle ni les économies de tokens en production.

Cette méthode a ses propres procédures, inspirées des mécanismes documentés dans
[BMAD](https://docs.bmad-method.org/workflow-map-diagram.html),
[Spec Kit](https://github.github.com/spec-kit/reference/agentic-sdd.html),
[OpenSpec](https://github.com/Fission-AI/OpenSpec) et
[Superpowers](https://github.com/obra/superpowers). Elle ne nécessite pas leur installation.
Le chargement progressif du contexte suit notamment les principes décrits par
[Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents).

Formats d'adaptation consultés : [Claude](https://code.claude.com/docs/en/skills),
[Cursor](https://cursor.com/help/customization/skills),
[Gemini](https://geminicli.com/docs/cli/custom-commands/),
[VS Code](https://code.visualstudio.com/docs/agent-customization/prompt-files),
[Cascade](https://docs.devin.ai/desktop/cascade/workflows).

## Choix d'architecture et socle SaaS

Le skill `architecture` peut partir d'une base MIT publique, d'une stack choisie librement ou du
projet existant. `method architecture` enregistre cette décision ; `method starters` présente
le catalogue. Les documents sont liés au choix exact et à ses contraintes. Voir le
[guide des boilerplates](boilerplates.md) pour la provenance, les commandes et la tâche de fondation.

## Gabarits PRD et user story

Les agents utilisent les mêmes rubriques à chaque rédaction. Les modèles installés sont
`.framework/method/templates/prd.md` et `.framework/method/templates/stories.md`. Le schéma JSON
embarqué détermine leur contenu et la validation à l'enregistrement : il n'y a pas de copie de
schéma à maintenir dans chaque skill.

| Document | Rubriques obligatoires |
| --- | --- |
| PRD | Problème/résultat, utilisateurs/parcours, périmètre/exclusions, exigences fonctionnelles, contraintes/qualité, succès/acceptation, hypothèses/décisions ouvertes |
| User story | Identité/résultat utilisateur, traçabilité du besoin, périmètre/exclusions, critères d'acceptation, dépendances/prérequis, notes pour les agents, vérifications, complexité/découpage |

Après création, réservation et démarrage de la tâche, créer une copie à remplir :

```bash
framework method template prd
framework method scaffold T-IDENTIFIANT --kind prd --file docs/produit/prd.md
framework method scaffold T-IDENTIFIANT --kind stories --file docs/dashboard/stories.md
```

`template` renvoie le modèle Markdown et son schéma dans une réponse JSON. `scaffold` crée le
fichier sans écraser un document existant et sans l'enregistrer comme un livrable déjà rédigé.
Le fichier doit appartenir au périmètre réservé de la tâche. Les skills `prd` et `stories`
utilisent ces gabarits ; l'utilisateur peut aussi les remplir lui-même.

Conserver le marqueur `Document: prd@1` ou `Document: stories@1` et les titres `##` exacts.
Remplacer tous les champs `{{ ... }}` ; utiliser des titres `###` pour ajouter du détail.
Une rubrique non applicable doit l'expliquer brièvement. Une hypothèse non résolue est déclarée,
pas remplacée par une certitude. Le PRD porte des identifiants `REQ-…` et `AC-…`, la story des
critères `AC-…` reliés au besoin. Le document de story reprend l'identifiant sélectionné,
`Complexité: N/5` et les notes déclarées par `method story`.

Exemple de critère utile : « AC-01 — Étant donné un utilisateur autorisé et une période sans
vente, quand il ouvre le dashboard, les indicateurs affichent zéro et l'état vide est explicite. »
Le gabarit sépare ce comportement attendu du choix de composant ou d'algorithme décrit dans le plan.

L'enregistrement refuse les sections manquantes, vides, dupliquées ou hors schéma, les champs
restés à remplir et l'absence d'identifiants de critères. La présence d'un identifiant ne prouve
pas que tous les critères sont testables ni que les exigences sont complètes : c'est le travail
de la revue de story. Les autres documents suivent leurs procédures, sans validation structurelle
stricte dans cette version.

Pour améliorer la structure commune dans le framework, modifier
`src/agentic_codage/assets/schemas/document-prd.json` ou `document-stories.json`, ajuster les
procédures/tests, puis réconcilier explicitement les copies générées et lancer
`framework adapters --check`. `framework adapters` crée les fichiers manquants mais refuse
d’écraser des instructions existantes différentes ; examiner leur diff avant de les remplacer.
Une évolution incompatible devra introduire une nouvelle version et une migration explicite :
le parseur actuel accepte uniquement la version 1. Ne pas modifier seulement les copies générées.

## Une story, une livraison et des notes pour l'agent

La convention de travail est **1 story sélectionnée = 1 tâche = 1 branche = 1 PR**. Un document
peut servir de catalogue, mais le contrat d'exécution sélectionne une seule story. Les workers du
contrôleur peuvent effectuer plusieurs travaux internes pour cette story ; ils ne créent pas une
PR chacun. L'agent chargé de shipping respecte la convention de branche/PR, que la CLI locale ne
peut pas imposer à des publications effectuées hors de son protocole.

En parcours Feature et Product, déclarer cette sélection avant la revue des stories :

```bash
framework method story T-IDENTIFIANT --id S-dashboard-periode --complexity 3 \
  --note "Réutiliser le composant DateRange existant" \
  --note "Les bornes de période sont en UTC et le montant est en centimes"
```

L'échelle, déclarative, est : 1 changement local simple ; 2 plusieurs fichiers bornés ; 3 plusieurs
composants aux interfaces stables ; 4 travail substantiel mais compris et borné ; **5 trop large ou
encore matériellement incertain**. Le niveau 5 bloque `method prompt plan` et la préparation à
l'exécution. Découper ou résoudre l'incertitude avec une justification ; une estimation faible ne
prouve pas qu'un travail sera facile. Modifier la story, ses notes ou sa complexité invalide sa
revue de préparation précédente.

Les notes donnent aux agents ce qu'un humain pourrait laisser implicite : composants à réutiliser,
unités, timezone, permissions, migrations, contrats et pièges connus. Les thèmes, traductions,
performances ou fondations UI transversales deviennent des prérequis explicites plutôt que des
hypothèses cachées. Un design system absent peut être une tâche préalable dite « story 0 » ;
son existence n'impose pas de le reconstruire. Les dépendances de tâches et leurs cycles sont
contrôlés par le framework, leur justesse métier par la revue.

La notice HTML se régénère depuis sa source Markdown avec `python scripts/build_notice.py` ;
installer `Markdown` dans un environnement de documentation isolé pour cette commande seulement.
Le framework lui-même garde zéro dépendance Python d'exécution.
