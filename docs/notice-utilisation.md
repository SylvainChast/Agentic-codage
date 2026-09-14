# Notice d’utilisation — développer avec des agents IA

**Agentic Codage 0.2.0 · Notice du 14 septembre 2026 · évolutions de coordination en version de travail**

Cette notice explique le fonctionnement livré, ses bénéfices et ses limites. Elle s’adresse au responsable produit qui pilote les agents et au développeur qui configure leur environnement. Les exemples de modèles, budgets et résultats ne constituent pas des mesures de performance.

## 1. Pourquoi ce framework est utile

Un agent de codage associe un modèle de langage à des outils : lire des fichiers, modifier du code, consulter Git et, selon ses permissions, exécuter des commandes. Le modèle propose les actions ; son outil d’exécution les réalise. La qualité du modèle compte, mais elle ne définit pas à elle seule le périmètre autorisé, les preuves attendues ou la coordination entre plusieurs agents.

Agentic Codage organise cette activité autour d’un résultat vérifiable. Sa force est de relier **besoin → contrat → exécutions → contrôles → revue → acceptation → coût**. Le projet conserve ces liens lorsque la conversation se termine ou lorsque l’on change d’outil.

| Problème fréquent | Réponse du framework | Limite à comprendre |
|---|---|---|
| L’agent étend le chantier sans prévenir | Contrat avec chemins modifiables et critères ; contrôle du plan et du diff | Les contrôles de fichiers ne détectent pas toute dérive fonctionnelle |
| Deux agents modifient les mêmes fichiers | Réservations entre tâches et worktrees séparés ; travaux recouvrants sérialisés dans le contrôleur | Des fichiers différents peuvent modifier la même interface métier |
| Une nouvelle session oublie les décisions | Décisions versionnées, journaux, contrats et extraction de contexte | L’agent doit consulter cette mémoire ; ce n’est pas un apprentissage automatique du modèle |
| L’agent annonce « terminé » trop tôt | Vérification exécutée, revue et acceptation distinctes | La pertinence des tests et de la revue reste déterminante |
| Une ancienne preuve est réutilisée après modification | Empreinte du contenu et du contrat ; contrôle de fraîcheur | Les fichiers ignorés et services externes ne sont pas attestés |
| Les tentatives se multiplient sans mesure | Limites d’appels, de tours et de temps ; coûts conservés | Le prix d’un appel en cours n’est pas prédit ni plafonné chez le fournisseur |
| Une solution semble économique en oubliant les échecs | Tous les runs restent imputés, y compris coordination, revue et reprises | Une facturation absente reste inconnue |
| Le projet dépend d’un seul outil | Contrats communs, règles d’éditeurs, CLI et pont JSON | Chaque outil doit effectivement charger les consignes et posséder les capacités nécessaires |

Cela peut rendre le développement plus contrôlable et les transmissions plus fiables. Le gain de vitesse ou d’argent doit être mesuré sur vos missions : davantage d’agents peut aussi ajouter du coût et du travail d’intégration.

## 2. Qui fait quoi ?

Il faut distinguer le **modèle**, le **rôle**, l’**outil qui exécute ses actions** et le **contrôleur du framework**.

| Acteur | Travail attendu | Ce qu’il ne décide pas seul |
|---|---|---|
| Utilisateur ou responsable produit | Définir le besoin, les critères, les modèles, les budgets et les autorisations | La réussite technique sans examiner les preuves |
| Orchestrateur LLM | Décomposer une mission en travaux avec dépendances et sous-périmètres | Élargir le contrat ou modifier lui-même le produit dans ce parcours |
| Exécutant `worker` | Réaliser un travail attribué dans son worktree | Réécrire les règles, s’auto-accepter ou lancer récursivement un nouvel essaim |
| Relecteur `reviewer` | Examiner le diff, les tests et chaque critère ; approuver ou demander une correction | Modifier le candidat pendant la revue |
| Arbitre `arbiter` | Orienter la reprise après un échec des contrôles ou un refus de revue | Dépasser les budgets ou résoudre automatiquement tout conflit Git |
| Contrôleur Python | Valider les réponses, réserver, ordonnancer, lancer les processus, mesurer, vérifier et enregistrer les états | Remplacer le jugement métier par une certitude automatique |

**L’orchestrateur LLM construit le plan ; le contrôleur logiciel applique les règles d’exécution.** Cette séparation évite de faire reposer les limites uniquement sur une promesse écrite dans un prompt.

Vous choisissez chaque modèle. Astra, Fable, Sol et Opus sont des exemples évoqués dans le projet, pas une liste autorisée ni une table d’identifiants. Fournir l’identifiant exact reconnu par la CLI choisie. Il n’y a pas de substitution silencieuse vers un modèle supposé meilleur ou moins cher.

Le même modèle peut occuper plusieurs rôles. Le contrôleur ouvre des sessions distinctes, mais cette séparation ne garantit pas une diversité de raisonnement. L’identité du relecteur reste déclarative ; une revue authentifiée sur votre plateforme Git complète le dispositif pour les livraisons importantes.

## 3. Les objets à connaître

| Objet | Exemple | Fonction |
|---|---|---|
| Tâche ou mission | `T-…` | Contrat : résultat, propriétaire, périmètre, critères, livrables, budget et dépendances |
| Interface | `I-…` | Convention versionnée de signature, unité ou schéma partagée entre agents |
| Exécution | `R-…` | Tentative d’implémentation, de coordination ou de revue avec résultat et coût |
| Session d’orchestration | `O-…` | Un lancement du contrôleur, son profil figé, son plan et ses appels |
| Travail délégué | Identifiant local comme `calcul` | Sous-travail d’un plan ; ce n’est pas automatiquement une nouvelle tâche `T-…` |
| Preuve | `E-…` | Résultats des commandes, logs, empreinte du code et du contrat |
| Revue | `V-…` | Verdict lié à une preuve et aux critères exacts de la tâche |
| Décision | `D-…` | Choix durable, justification, chemins concernés et contrôles associés |
| Finding | `F-…` | Problème identifié et suivi jusqu’à sa résolution |
| Exception | `X-…` | Dérogation documentée avec propriétaire et échéance, sans désactivation automatique des contrôles |

Une tâche peut avoir plusieurs sessions et beaucoup d’exécutions. Les coûts des sessions abandonnées restent attachés à cette tâche. Son acceptation porte sur tous ses livrables : pour accepter deux résultats séparément, créer deux tâches.

## 4. À quoi sert exactement le fichier HTML ?

`docs/carte-du-code.html` est la **vue humaine de référence** du projet. Il permet de comprendre le travail sans lire chaque JSON ni retrouver les conversations d’origine.

Les agents alimentent les fiches de `.framework/`, généralement via la CLI. Le générateur les lit, les valide et assemble une page autonome :

```text
Code Git + politique + décisions + contrats + runs + preuves + revues
                              ↓
                        framework map
                              ↓
                    docs/carte-du-code.html
```

Cette architecture évite que plusieurs agents réécrivent simultanément un grand fichier HTML. Les JSON sont les sources structurées ; le HTML est leur présentation. **Une modification manuelle du HTML n’actualise pas les fiches et sera perdue à la régénération.**

### Ce que l’on peut y lire

| Vue | Question à laquelle elle répond |
|---|---|
| Vue d’ensemble | Quelles missions restent ouvertes ? Les fiches sont-elles cohérentes ? |
| Missions | Quel résultat est attendu, par qui, dans quel périmètre ? |
| Décisions | Quels choix doivent être respectés et pourquoi ? |
| Risques | Quels problèmes et exceptions sont enregistrés ? |
| Orchestration | Quel modèle a été choisi, quel plan a tourné, quels appels et quel état ? |
| Preuves | Quels contrôles ont réellement tourné et quelles revues sont enregistrées ? |
| Interfaces | Quelles versions et conventions les agents doivent-ils respecter ? |
| Coûts | Combien connaît-on de dépenses et que vaut le coût par résultat accepté ? |
| Journaux | Qu’ont fait les sessions et quelle suite ont-elles laissée ? |

La recherche filtre les fiches. Le détail de chaque fiche expose ses références. Les logs complets restent dans le dépôt : le HTML n’est pas un export complet de tous les artefacts.

### Les gestes utiles

```bash
framework map
framework map --check
framework lease list
```

La première commande régénère la page ; la deuxième vérifie que ses données correspondent encore au projet. Ouvrir ensuite le fichier dans un navigateur et actualiser la page après régénération. Aucun serveur ni CDN n’est nécessaire. Sur GitHub, le lien vers le fichier affiche généralement son code source.

Les réservations vivantes sont consultables avec `lease list`, pas dans l’instantané. Le HTML ne lance ni n’arrête les agents. Ce n’est ni un tableau de bord temps réel ni une analyse automatique de toutes les classes et fonctions du code.

Pour un agent, `framework context src/pricing.py` est souvent plus pertinent que l’ingestion du HTML entier : la commande sélectionne les tâches, décisions, problèmes et transmissions concernant ce chemin. Dans le contrôleur, les appels reçoivent leur contrat et les informations propres au rôle ; une lecture exhaustive de toute la mémoire n’est pas injectée automatiquement.

Le fichier HTML peut embarquer des informations internes du projet. Le partager revient à partager ces informations ; il n’effectue pas de filtrage de confidentialité pour chaque destinataire.

## 5. Installer le framework dans une application

Le dépôt du framework contient déjà sa propre installation. **Ne pas y relancer `init`.** Pour équiper votre application :

```bash
# Dans le dépôt Agentic-Codage :
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
framework --help

# Dans le dépôt Git de votre application :
cd /chemin/vers/application
framework init --name "Mon application" --currency EUR
```

Sous Windows, utiliser `py -3 -m venv .venv`, puis `.venv\Scripts\Activate.ps1`. Les exemples multilignes suivants utilisent la syntaxe d’un shell Unix ; sous PowerShell, les saisir sur une ligne ou adapter leur continuation.

Sans installation, depuis les sources du framework, `python3 bin/framework` remplace `framework`. Pour cibler un autre projet depuis ces sources, ajouter l’option globale `--root /chemin/vers/application` avant la sous-commande.

L’initialisation refuse d’écraser des instructions existantes. Réconcilier celles du projet avec le contrat commun. Les points d’entrée sont `AGENTS.md`, `CLAUDE.md`, les règles Cursor, les instructions Copilot et les autres adaptateurs. Les skills `swarm-deliver`, `swarm-review` et `swarm-orchestrate` décrivent les procédures spécialisées.

### Configurer les vrais contrôles

Dans `.framework/policy.json`, remplacer la vérification d’amorçage, volontairement en échec, par les commandes pertinentes pour votre application. Exemple de **champ `checks`**, à intégrer dans la politique complète :

```json
"checks": [
  {
    "name": "tests",
    "argv": ["{python}", "-m", "unittest", "discover", "-s", "tests", "-v"],
    "timeout_seconds": 180
  }
]
```

Choisir les tests adaptés au produit : comportement métier, régressions, intégration, analyse statique et contrôles de sécurité selon la stack. Une commande est un tableau d’arguments ; `&&`, les pipes et les variables shell ne sont pas interprétés automatiquement. `{python}` en première position désigne l’interpréteur du framework.

Les dépendances ignorées par Git ne sont pas copiées dans les worktrees. Prévoir une procédure de vérification reproductible depuis un checkout neuf. Les commandes de test doivent aussi éviter de modifier les sources et de rendre elles-mêmes la preuve obsolète.

## 6. Choisir le mode de travail

**Mode accompagné :** vous travaillez avec un agent dans votre outil habituel. Les agents ou l’opérateur exécutent les commandes du cycle de vie. La CLI ne lance pas le modèle pour eux. Ce mode convient aussi aux modifications des instructions, de la CI et du framework lui-même.

**Mode orchestré :** le contrôleur lance explicitement les processus des modèles configurés, distribue les travaux, enregistre les appels, vérifie et demande la revue. Il nécessite une CLI Codex ou Claude fonctionnelle, ou un pont JSON développé pour un autre outil.

Les règles pour Cursor, Copilot ou Gemini permettent de suivre le protocole accompagné ; leur présence ne constitue pas un adaptateur de lancement automatique pour ces outils. Un modèle sans accès aux fichiers ni aux commandes peut préparer une proposition, mais ne peut pas prétendre avoir exécuté les contrôles.

Pour une petite correction évidente, le mode accompagné peut être plus économique. L’orchestration devient intéressante lorsque la mission a plusieurs sous-problèmes, des interfaces explicites et une vérification fiable.

## 7. Parcours orchestré : du besoin au code intégré

### Étape 1 — Rédiger un contrat précis

Exemple : ajouter un calcul TTC avec refus des valeurs négatives.

```bash
framework task create --title "Ajouter le calcul TTC" --owner equipe-pricing \
  --scope src/pricing.py --scope tests/test_pricing.py --resource api:pricing \
  --criterion "Le total de 100 à 20 pour cent vaut 120" \
  --criterion "Un montant négatif est refusé" \
  --deliverable "Calcul TTC testé" --budget-minor 2500 --max-runs 12
```

Conserver l’identifiant retourné. `T-IDENTIFIANT` dans les exemples doit être remplacé par cet identifiant, sans en inventer un. Ici, `2500` signifie 25 EUR ; c’est un budget d’exemple à adapter, pas un prix estimé.

Les chemins sont littéraux, sans joker. `src/pricing` couvre ses descendants, pas `src/pricing-old`. Une ressource comme `api:pricing` exprime une interface partagée entre tâches. Les ressources sont réservées au niveau de la tâche ; les travaux internes du plan sont ordonnancés selon leurs chemins et dépendances.

### Étape 2 — Choisir les modèles

```bash
framework orchestration init --adapter codex --model IDENTIFIANT_CHOISI
framework orchestration set-role worker --adapter codex --model IDENTIFIANT_EXECUTANT
framework orchestration set-role reviewer --adapter claude --model IDENTIFIANT_RELECTEUR
framework orchestration config
framework orchestration doctor
```

`init` attribue le choix initial aux quatre rôles ; les commandes `set-role` changent uniquement le rôle nommé. L’arbitre conserve donc ici le modèle initial. Les noms en majuscules sont à remplacer par des identifiants disponibles dans vos comptes.

`doctor` vérifie la présence des exécutables. Il ne valide pas les comptes, permissions ou modèles auprès des fournisseurs et ne fait pas d’appel payant.

Le profil `.framework/orchestration.json` définit par défaut 2 travailleurs simultanés, 2 tours, 8 travaux maximum par plan et 600 secondes par appel. Consulter [le guide d’orchestration](orchestration.md) pour les plafonds et l’exigence facultative de modèle observé.

### Étape 3 — Enregistrer la base dans Git

Examiner puis committer le code de départ, les tests, les instructions, la politique, le profil et le contrat. Le contrôleur exige une base committée ; un dossier non enregistré en cours de modification n’est pas une base de lancement.

Dans un dépôt protégé, intégrer d’abord le contrat par une PR de cadrage. Le contrôle `framework check --base SHA --task T-IDENTIFIANT` vérifie le périmètre contre ce contrat de référence. Il n’est pas automatiquement transformé en règle obligatoire de votre hébergeur Git par l’installation.

### Étape 4 — Lancer

```bash
framework orchestration run T-IDENTIFIANT
```

Cette commande utilise les comptes configurés des CLI et peut engager des coûts. Elle reste au premier plan : le framework n’est pas un service permanent fonctionnant indépendamment de ce processus.

### Étape 5 — Comprendre ce qui se déroule

1. Le contrôleur vérifie la configuration et la base, verrouille la tâche et acquiert son bail.
2. Il crée un candidat Git isolé et demande un plan à l’orchestrateur dans un autre worktree.
3. Il contrôle les identifiants, le nombre de travaux, les dépendances sans cycle et les sous-périmètres.
4. Il lance les travailleurs prêts dans leurs propres worktrees. Les chemins recouvrants ne sont pas traités dans le même groupe parallèle.
5. Il contrôle les fichiers modifiés et le HEAD Git, puis crée lui-même les commits privés et applique les patchs au candidat. Le travailleur ne doit pas committer.
6. Après chaque lot, l’orchestrateur inspecte le candidat et doit autoriser la suite au point de contrôle. Les travaux dépendants reçoivent ensuite le code, le plan, les interfaces figées et les comptes rendus de leurs prédécesseurs.
7. Il exécute les commandes de la politique sur le candidat assemblé et conserve leurs logs.
8. Si elles passent, une session de relecture examine le diff, la preuve et chaque critère exact.
9. Une approbation produit l’état `ready`. Un échec des contrôles ou un refus peut déclencher un arbitrage puis un nouveau plan, dans les limites restantes.

Une erreur de transport, un modèle inattendu, une sortie de périmètre ou un conflit de patch bloque la session. Le moteur ne corrige pas indistinctement toutes les erreurs et ne lance pas une conversation libre entre agents : il organise des transmissions structurées.

Les instructions et métadonnées du framework, les entrées d’agents protégées, les chemins commençant par `.git` — dont `.github` et `.gitignore` — et le HTML de référence sont exclus des écritures déléguées. Leur évolution passe par un parcours accompagné avec revue.

### Exemple de parallélisme utile

```text
Plan
 ├─ A : calcul métier, src/pricing.py
 └─ B : formatage de facture, src/invoice_format.py
             ↓ A et B terminés
      Point de contrôle orchestrateur
             ↓ continuer
      C : tests d’intégration du parcours
             ↓
      Point de contrôle → contrôles du produit → revue
```

A et B peuvent avancer ensemble si leur contrat d’interface est clair. C dépend des deux. Le planificateur choisit ce découpage ; le framework ne découvre pas automatiquement toutes les dépendances sémantiques. Si tous les travaux réclament `src`, ils seront sérialisés : un périmètre trop large supprime le bénéfice du parallélisme.

### Contrats d’interface et points de contrôle

Avant de déléguer un dashboard relié à une API, préciser dans un contrat `I-…` les champs, unités,
formats, signatures et erreurs attendus. Importer sa fiche avec `framework import interfaces prix-v1.json`
et référencer sa version avec `task create --interface I-prix-v1`. Un exemple complet figure dans
le [guide de coordination](coordination.md). Les contrôles nommés dans cette fiche doivent exister
dans la politique ; ils s’exécutent à la vérification finale.

Chaque travailleur reçoit exactement les mêmes versions pour sa tâche et doit renvoyer leurs
références avec empreintes dans `acknowledged_interfaces`. Il reçoit aussi le plan et les comptes
rendus des lots précédents. Une ancienne version ou une référence manquante bloque le lot.

S’il estime qu’une interface doit changer, il renseigne `change_requests`. Le contrôleur conserve
la demande et bloque avant intégration du lot ; le pilote révise le contrat et lance une nouvelle
session sur la base commitée. Une version 2 est une nouvelle fiche qui référence sa version 1.
Les agents ne doivent pas changer silencieusement les unités pour faciliter leur propre travail.

Après chaque lot intégré, le modèle choisi pour l’orchestrateur inspecte les modifications et
renvoie `continue` ou `block`. C’est un appel supplémentaire facturé à la tâche. Ce contrôle
intermédiaire est une inspection par le modèle ; les tests automatiques et la revue finale restent
nécessaires. Les points de contrôle et comptes rendus sont conservés dans la fiche de session.

Les JSON des worktrees restent des copies locales. La transmission se fait par le contrôleur
entre les lots ; ce n’est pas une messagerie instantanée. En mode accompagné, le pilote doit
organiser lui-même ces transmissions. Une interface non déclarée peut encore être oubliée :
aucun protocole ne remplace un cadrage clair et des tests utiles.

### Étape 6 — Examiner le résultat

```bash
framework orchestration list
framework orchestration show O-IDENTIFIANT
framework costs
framework map
```

Dans un second terminal, `list` permet de retrouver une session en cours. Examiner ses appels, son plan, son message final et ses références de preuve/revue. `git worktree list` permet de localiser les candidats conservés.

| État de session | Interprétation |
|---|---|
| `running` | Contrôleur actif, ou état resté ainsi après un crash brutal à diagnostiquer |
| `blocked` | Une limite ou un échec empêche la suite ; lire `message` et les traces |
| `cancelled` | Le contrôleur a enregistré l’annulation |
| `ready` | Le candidat a passé les contrôles et reçu une revue favorable ; il n’est pas intégré |
| `integrated` | Le candidat a été appliqué au checkout et la tâche acceptée localement |

### Étape 7 — Intégrer explicitement

Après examen du résultat et dans le cadre de votre autorisation :

```bash
framework orchestration integrate O-IDENTIFIANT --actor responsable-produit
framework map
```

Le contrôleur vérifie que le code de départ, le contrat, le candidat et les preuves sont toujours compatibles. Il applique le patch à votre répertoire de travail et enregistre l’acceptation. **Il ne committe pas sur votre branche, ne pousse pas, ne crée pas de PR et ne déploie pas.** Terminer ensuite le processus Git et la CI prévus par votre équipe.

Éviter de modifier ce checkout pendant la session. Même une modification indépendante peut invalider sa base ou ses preuves. Garder les worktrees jusqu’à l’intégration et conserver les traces utiles avant tout nettoyage.

## 8. Parcours accompagné : travailler dans son IDE

Créer le même contrat, le committer selon votre workflow et travailler dans un worktree dédié. Après lecture des consignes et du contexte :

```bash
framework lease acquire T-IDENTIFIANT --owner equipe-pricing --ttl 3600
framework task start T-IDENTIFIANT --actor equipe-pricing
framework context src/pricing.py
```

Demande type à l’agent :

> Réalise la tâche T-IDENTIFIANT. Lis les instructions et les décisions pertinentes. Respecte les chemins et les critères du contrat. Enregistre les résultats et les coûts disponibles, exécute les contrôles et prépare une transmission à un relecteur distinct.

Après son travail, enregistrer les faits réellement observés :

```bash
framework run record T-IDENTIFIANT --actor equipe-pricing --model "MODELE_OBSERVE" \
  --purpose implementation --outcome succeeded --cost-source unknown \
  --cost-note "Montant de facturation indisponible" \
  --summary "Décrire ici les changements réellement réalisés" \
  --next-step "Vérification puis revue distincte"
framework check
framework verify T-IDENTIFIANT
framework task submit T-IDENTIFIANT --actor equipe-pricing
```

Ne pas copier l’état `succeeded` si la tentative a échoué : enregistrer `failed`, `blocked` ou `cancelled` selon les faits. Une nouvelle tentative crée un nouveau run ; rappeler `task start` pour vérifier les limites avant de la lancer.

Un vrai relecteur distinct inspecte ensuite le diff et les critères. Comptabiliser également son exécution via `run record --purpose review` avec ses résultats et coûts réels. **Après une revue favorable effective**, enregistrer son verdict avec la preuve retournée par `verify` :

```bash
framework review record T-IDENTIFIANT --reviewer relecteur-b --verdict approve \
  --evidence E-IDENTIFIANT \
  --criterion "Le total de 100 à 20 pour cent vaut 120" \
  --criterion "Un montant négatif est refusé" \
  --summary "Décrire les vérifications et conclusions réelles de la revue"
framework task accept T-IDENTIFIANT --review V-IDENTIFIANT --actor responsable-produit
framework map
```

Ces commandes enregistrent une revue ; elles ne l’effectuent pas à la place du relecteur. Si elle demande des changements, utiliser `request_changes`. Toute correction requiert une nouvelle preuve et une nouvelle revue. La CLI exige une preuve passée même pour enregistrer ce verdict structuré ; conserver d’abord les diagnostics de tests échoués dans les runs ou findings.

Ne pas doubler ces enregistrements dans une session orchestrée : le contrôleur y gère déjà les baux, appels, coûts et preuves.

## 9. Comprendre les coûts et les limites

Pour mesurer la livraison d’un dashboard, d’un module ou d’une feature, créer une tâche pour ce
résultat et conserver tous ses travaux et reprises sous cet identifiant. Utiliser :

```bash
framework costs --task T-IDENTIFIANT
```

Le rapport ventile les dépenses par finalité, rôle, modèle, travail et session. Il additionne
l’implémentation, les échecs, les corrections, la coordination, les points de contrôle et la revue,
ainsi que l’infrastructure et le temps humain imputés. Le coût d’une autre tâche n’y est pas ajouté.

Avant acceptation, le montant connu est un encours et `delivery.total_cost_minor` reste vide.
À l’acceptation, la liste des exécutions est figée : le total de livraison est calculable si leurs
coûts LLM sont tous renseignés. Les estimations restent signalées, les montants inconnus ne valent
jamais zéro. Les exécutions ajoutées ensuite apparaissent séparément. Les anciennes acceptations
sans liste figée sont signalées comme telles. Voir les [détails de calcul](costs.md).

La carte affiche ce montant dans **Coût de livraison accepté**. Il permet de comparer le coût
complet enregistré pour plusieurs résultats, en tenant compte de leur taille et de leur qualité.


Le budget n’est pas le coût. Il borne le lancement de nouveaux appels sur la base des montants déjà connus. Un abonnement n’équivaut pas à une consommation gratuite.

- `actual` : montant rapporté ou relevé comme réel, avec provenance ; il ne constitue pas une facture certifiée par le framework.
- `estimate` : allocation calculée selon une méthode explicite.
- `unknown` : montant absent ; les ratios concernés deviennent non calculables.

Les montants sont des entiers en unités mineures, dans une seule devise à deux décimales. Les coûts humains et d’infrastructure ne sont pas mesurés automatiquement ; leurs valeurs par défaut correspondent à une absence d’imputation.

Exemple fictif : une tâche acceptée a coûté 8 EUR pour ses travailleurs, 2 EUR de planification, 3 EUR de revue et 4 EUR de reprises. Son coût connu est **17 EUR**, pas 8 EUR. Si elle livre deux éléments acceptés ensemble, le ratio est 8,50 EUR par élément. Une autre tâche abandonnée à 6 EUR fait monter le ratio global du portefeuille à **23 / 2 = 11,50 EUR**. Si un appel n’a pas de coût renseigné, ce ratio global reste inconnu.

`framework costs` expose aussi `by_role` et `by_orchestration`. Les livrables comptés sont ceux du contrat accepté : multiplier artificiellement les livrables fausse la métrique. Définir des unités comparables et utiles au produit.

`max_runs` compte les exécutions, y compris coordination et revue. Un tour avec un planificateur, trois travailleurs et un relecteur consomme cinq appels. Un second tour semblable précédé d’un arbitrage porte le total à onze. `max_rounds` borne les cycles ; `max_parallel` borne les travailleurs simultanés. Ce sont trois limites différentes.

Le contrôleur réserve les places d’appels en cours pour `max_runs`, mais il ne réserve pas un prix futur. Des appels simultanés peuvent dépasser le montant restant. Un plafond financier strict doit aussi être configuré chez le fournisseur.

## 10. Intervenir lorsqu’une mission rencontre un problème

```bash
framework orchestration feedback O-IDENTIFIANT --message "Précision pour le prochain plan"
framework orchestration cancel O-IDENTIFIANT
```

Le feedback est lu au prochain tour de planification. Il ne modifie ni l’appel déjà en cours ni le contrat. S’il n’y a pas de nouveau tour, il ne sera pas exploité par un nouveau plan.

L’annulation est surveillée pendant les appels et avant les nouveaux appels. Un contrôle produit déjà lancé reste borné par son propre délai. Elle n’efface pas les coûts engagés. Sous Windows, la terminaison concerne le processus direct ; l’isolation des descendants dépend de l’environnement.

| Situation | Conduite utile |
|---|---|
| Exécutable absent | Corriger PATH ou le chemin explicite de la commande, puis `doctor` |
| Modèle refusé ou inattendu | Vérifier l’identifiant et l’accès du compte ; autoriser explicitement une version observée si c’est bien le choix voulu |
| Coût inconnu | Conserver `unknown` ; compléter ensuite avec une provenance et sans double comptage |
| Périmètre insuffisant | Revoir et committer le contrat, puis lancer une nouvelle session |
| Tests en échec | Lire les logs, corriger la cause dans le budget ; ne pas affaiblir les tests pour obtenir le vert |
| Base modifiée après lancement | Examiner le candidat conservé et repartir d’une nouvelle base ; pas de rebase automatique des preuves |
| Session bloquée | Lire sa cause et conserver les tentatives ; un nouveau `run TASK` repart du code committé |
| Crash brutal | Inspecter les processus, l’état, les worktrees et les verrous ; ne retirer un verrou orphelin qu’après avoir vérifié qu’aucun contrôleur ne tourne |

Une reprise interne après refus travaille sur le candidat du tour précédent. Un **nouveau lancement après blocage** crée une nouvelle session depuis le checkout committé : il ne récupère pas implicitement le travail partiel. Les budgets de la tâche, eux, restent cumulatifs.

## 11. Les garanties à ne pas confondre

- `check` valide les fiches et leurs liens ; il ne teste pas le comportement du produit.
- `verify` exécute les commandes configurées ; il ne choisit pas à votre place les bons tests.
- Une revue examine le résultat ; une identité différente dans un JSON n’authentifie pas son indépendance.
- `accepted` signifie une acceptation locale appuyée sur les preuves ; ce n’est pas un déploiement ni une certification.
- Une réservation est coopérative et locale au clone ; elle n’est pas un verrou universel entre ordinateurs.
- Un worktree isole le candidat Git ; il n’isole pas les secrets, le réseau et tout le système de fichiers.
- Le pont JSON générique et les commandes de test sont du code de confiance exécuté avec les droits du processus. Les restrictions natives dépendent des CLI utilisées.
- Les projets contenant des liens symboliques dans les sources ne sont pas pris en charge par le lancement automatique actuel.
- Les adaptateurs natifs ont été validés sur commandes et réponses représentatives, sans démonstration payante de bout en bout avec des comptes fournisseurs.

Le framework apporte des éléments utiles à une revue technique : traçabilité des décisions, tests exécutés, provenance des coûts et historique des résultats. Une due diligence exige aussi des preuves adaptées au produit : architecture, dépendances, sécurité, exploitation, propriété intellectuelle et continuité opérationnelle. Le nombre de tests ou de lignes de code ne constitue pas une certification « Grade A ».

## 12. Routine conseillée pour une équipe

**Avant :** préciser un résultat, ses critères et ses interfaces ; choisir le mode adapté ; préparer les contrôles, modèles, autorisations et budgets ; enregistrer la base Git.

**Pendant :** surveiller les états et les transmissions ; traiter les ambiguïtés de contrat ; conserver les échecs ; intervenir sur une cause concrète sans multiplier automatiquement les agents.

**Après :** examiner le diff, la preuve et la revue ; accepter et intégrer selon le parcours ; terminer la CI et la livraison du produit ; régénérer le HTML ; comparer coût, délai, reprises et effort humain.

Le premier indicateur utile est le nombre de résultats acceptés avec peu de corrections. La taille de l’essaim et le nombre d’appels sont des moyens, pas des objectifs.

## 13. Du besoin au code : la méthode et les skills

Le framework fournit maintenant des procédures pour préparer le travail des agents. L'objectif
est de faire circuler un besoin précis, des décisions traçables et des critères vérifiables,
sans imposer un PRD complet à chaque petite correction.

| Parcours | Quand l'utiliser | Documents nécessaires avant le code |
| --- | --- | --- |
| Express | Correction claire et limitée | Plan |
| Feature | Fonctionnalité dans un produit existant | Story revue, conception et plan |
| Product | Nouveau produit ou cadrage substantiel | PRD, architecture, story revue, conception et plan |

L'option `--ui` ajoute un design system. Réutiliser celui du produit quand il existe. Le créer
comme prérequis, souvent appelé « story 0 », quand les écrans n'ont pas encore de base commune.
La recherche est ciblée sur une incertitude ; elle n'est pas imposée pour chaque tâche.

### Les onze procédures

| Étape | Travail confié à l'agent |
| --- | --- |
| `research` | Répondre à une incertitude avec des sources et une conclusion limitée aux preuves |
| `prd` | Définir le problème, les utilisateurs, les exigences et les critères de succès |
| `architecture` | Fixer les responsabilités, interfaces, contraintes et décisions structurantes |
| `design-system` | Définir les composants, états et règles visuelles partagés |
| `stories` | Découper le besoin en résultats livrables avec critères testables et notes pour l'agent |
| `story-review` | Faire relire le cadrage par un acteur distinct de ses auteurs |
| `design` | Concevoir la solution de la story choisie dans l'architecture existante |
| `plan` | Décrire les changements, dépendances et vérifications nécessaires |
| `execute` | Coder dans le périmètre et le worktree réservés |
| `review` | Examiner le diff, les critères et les preuves de vérification |
| `ship` | Préparer la PR, puis suivre sa publication et sa CI avec les outils autorisés |

Dans Codex, sélectionner par exemple `$swarm-prd` ou `$swarm-stories`. Dans Claude/Cursor,
les entrées correspondantes sont `/prd` et `/stories`. Copilot, Gemini et Cascade disposent
aussi de fichiers d'adaptation. La disponibilité dans le menu dépend de l'hôte et de ses noms
réservés ; tous les agents capables de lire des fichiers et d'utiliser le terminal peuvent
utiliser `framework method prompt ETAPE --task T-IDENTIFIANT`.

Un skill est une procédure chargée par l'agent courant. Il ne lance pas automatiquement onze
modèles, ne sélectionne pas un fournisseur et ne change pas votre modèle. Le moteur d'orchestration
reste le mécanisme distinct qui délègue le développement, avec les modèles que vous avez choisis.

### Choisir une boilerplate libre ou son architecture

La commande d'architecture permet maintenant de sélectionner un socle public sous licence MIT,
de définir sa propre stack ou de conserver un projet existant. L'utilisateur garde le choix.

| Profil | Usage envisagé |
| --- | --- |
| `nextjs-saas` | Base Next.js/PostgreSQL avec authentification, équipes, abonnements et dashboard ; à compléter selon le produit |
| `open-saas` | Base React/Node.js avec Wasp, authentification, paiements, emails et tâches de fond |
| `fastapi-react` | Base FastAPI/Python et React, avec authentification, tests et outillage ; logique SaaS spécifique à ajouter |

Dans les hôtes compatibles, demander `/architecture --boilerplate nextjs-saas`,
`/architecture --custom "Django, PostgreSQL"` ou `/architecture --existing`.
Dans Codex, utiliser `$swarm-architecture` en précisant le choix. L'agent traduit la demande
vers la CLI et l'enregistre sur la tâche :

```bash
framework method starters
framework method architecture T-IDENTIFIANT --boilerplate nextjs-saas
framework method prompt architecture --task T-IDENTIFIANT
```

La sélection ne crée pas d'application. Elle prépare un choix traçable. Pour une boilerplate,
l'agent examine le dépôt réel, note le commit choisi avec `--revision`, puis enregistre le document
d'architecture correspondant. Une modification de stack, de révision ou de contraintes exige
une révision du cadrage. Une tâche de fondation prend ensuite en charge l'importation, la
configuration et la validation du SaaS dans le projet applicatif.

On peut aussi construire notre propre boilerplate à partir d'un socle MIT ou d'une architecture
originale. Cela nécessite un livrable de développement distinct : la commande ne génère pas
à elle seule un équivalent complet de ShipSaaS. Le coût du socle est suivi dans sa tâche, puis
ses documents sont réutilisés par les features. Le code libre peut s'appuyer sur des services
externes payants ; ces frais restent à configurer et mesurer.

Voir le [catalogue, les sources et le mode d'emploi](boilerplates.md). Le contenu des projets
publics est présenté d'après leur documentation ; leur sélection ne vaut pas audit de qualité.

### Un schéma commun pour chaque PRD et chaque story

Les modèles Markdown sont installés dans `.framework/method/templates/`. Les schémas JSON
versionnés définissent leurs rubriques obligatoires. Les skills les utilisent systématiquement.

Le **PRD** décrit le problème, les utilisateurs, le périmètre, les exigences `REQ-…`, les contraintes,
les critères de succès `AC-…` et les décisions encore ouvertes. La **story** décrit un résultat
utilisateur précis, sa traçabilité, son périmètre, ses critères `AC-…`, ses dépendances, les notes
pour l'agent, les vérifications attendues et sa complexité.

Après création et démarrage d'une tâche réservée, les commandes suivantes créent les copies
à rédiger dans son périmètre :

```bash
framework method init T-IDENTIFIANT --track product --ui
framework method scaffold T-IDENTIFIANT --kind prd --file docs/produit/prd.md
framework method scaffold T-IDENTIFIANT --kind stories --file docs/produit/stories.md
```

Le fichier créé est un gabarit, pas un document terminé. L'agent remplace les champs à compléter,
conserve les titres obligatoires et précise les inconnues. L'enregistrement refuse les rubriques
manquantes ou vides et les champs de gabarit restants. La revue évalue ensuite la qualité du contenu.
Le [guide de la méthode](methodologie.md) détaille le schéma et la manière de le faire évoluer.

### Une story correspond à une livraison

La convention est **une story exécutable = une tâche = une branche = une PR**. Une feature trop
grosse se décompose en plusieurs stories reliées par leurs dépendances. Le CLI contrôle la story
sélectionnée et sa complexité ; le respect effectif du découpage en PR fait aussi partie de la revue.

```bash
framework method story T-IDENTIFIANT --id S-dashboard-periode --complexity 3 \
  --note "Réutiliser le composant de période et les contrôles de droits existants"
```

Les notes donnent à l'agent le contexte implicite : composants existants, unités, conventions,
permissions, cas limites. La complexité va de 1, changement local simple, à 5, travail trop large
ou encore incertain. **Le niveau 5 bloque la planification et l'exécution** jusqu'à découpage ou
résolution justifiée de l'incertitude. Changer arbitrairement la note ne réduit pas le travail.

### Comment les documents protègent le développement

Après rédaction, `method record` enregistre une fiche `A-…` avec l'empreinte du fichier et les
révisions de ses documents d'entrée. `method use` réutilise un document commun. Une revue de
story crée une fiche `Q-…`, liée à cette révision et au contrat de la tâche.

En Product, la chaîne relie PRD, architecture, story, conception et plan. Si le PRD change,
le framework détecte que les documents dépendants sont périmés. L'agent doit réexaminer les
conséquences, enregistrer les révisions à jour et renouveler les revues concernées. Une ancienne
revue ne valide pas automatiquement de nouvelles exigences.

```bash
framework method status T-IDENTIFIANT
framework method gate T-IDENTIFIANT
framework method prompt execute --task T-IDENTIFIANT
```

`status` explique les manques ; `gate` autorise ou refuse le passage au développement selon les
contrôles déclarés. Le moteur vérifie ce prérequis avant son lancement, avant chaque nouvel appel et avant
intégration ; `verify` le contrôle à nouveau. Un refus de revue intervenu pendant la session
bloque donc la suite. Les travailleurs ne peuvent pas modifier les documents de cadrage enregistrés. Chaque agent reçoit un contexte adapté à l'étape. Les extraits sont limités par défaut
à 12 000 caractères de documents, avec les chemins vers le détail et un signal de troncature.
Cette limite ne mesure ni tous les tokens du prompt ni les coûts réels du modèle.

La carte HTML possède une vue **Cadrage** pour retrouver les documents enregistrés et leurs revues.
Elle reste un instantané régénéré par `framework map` ; la commande `method status` calcule l'état
courant. Les fichiers JSON assurent les liens et les contrôles, le Markdown expose le contenu,
et le HTML permet à l'humain de consulter ces informations.

### Le cadrage fait partie du coût de livraison

Chaque exécution peut porter une étape avec `run record --stage prd`, `--stage stories`,
`--stage execute`, etc. `framework costs --task T-IDENTIFIANT` ventile ainsi les coûts du cadrage,
du développement, des corrections et des revues. Les coûts absents restent inconnus.

Le PRD commun à plusieurs features conserve son coût dans sa tâche de cadrage : réutiliser son
identifiant n'ajoute pas plusieurs fois la même facture. Le total du projet inclut ce coût commun.
Le coût d'une feature ne lui en réalloue pas automatiquement une quote-part. Pour un dashboard
découpé en plusieurs tâches, cette version expose les coûts de chaque livraison et le total projet ;
elle ne fournit pas encore un agrégat financier nommé regroupant plusieurs tâches.

L'acceptation fige les exécutions incluses dans le coût de livraison. Une opération de shipping
réalisée après cette acceptation figure séparément. En mode accompagné, enregistrer les étapes
à inclure avant l'acceptation ; l'intégration orchestrée conserve sa propre séquence d'acceptation.

`method ship` prépare une description locale de PR avec critères, preuves et coûts. La publication,
la CI, la fusion et le déploiement restent des opérations distinctes. Le skill guide l'agent dans
leur exécution selon votre demande et les outils disponibles. Un fichier de PR préparé ne prouve
pas qu'une PR a été ouverte ou que la CI a réussi.

## Pour approfondir

- [Bases SaaS libres et choix d’architecture](boilerplates.md)
- [Méthode, skills et gabarits PRD/story](methodologie.md)
- [Guide des commandes d’orchestration](orchestration.md)
- [Parcours accompagné détaillé](workflow.md)
- [Formules et provenance des coûts](costs.md)
- [Architecture et empreintes](architecture.md)
- [Compatibilité des outils](adapters.md)
- [Exploitation et protections Git](operations.md)
- [Qualité et preuves](quality.md)
- [Limites de la version](limitations.md)
- [Carte HTML du dépôt](carte-du-code.html)

Pour essayer le mécanisme sans appeler de modèle, depuis le dépôt du framework :

```bash
python3 examples/demo.py
python3 examples/orchestration_demo.py
python3 examples/method_demo.py
```

Les modèles, verdicts et montants de ces démonstrations sont simulés explicitement. Les modifications Git et contrôles locaux de leur parcours sont réellement exécutés dans des projets temporaires.
