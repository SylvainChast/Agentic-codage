# Coûts par exécution, tâche et livrable conforme

## Unités et provenance

Un projet utilise une seule devise ISO à trois lettres et deux décimales. Les montants sont des
entiers en unités mineures : EUR 12,34 = `1234`. La v0.1 ne prend pas en charge les devises sans
décimales ou à trois décimales, ni la conversion automatique. La devise est déclarée par l’opérateur.

Chaque **run** décrit une exécution d’implémentation, de revue ou de coordination :

| Champ | Sens |
|---|---|
| `llm_cost_minor` | Coût LLM de cette exécution, entier ou `null` |
| `cost_source` | `actual` observé, `estimate` calculé, `unknown` indisponible |
| `cost_note` | Origine de la facture, méthode d’allocation ou raison de l’absence |
| `infra_cost_minor` | Infrastructure imputée à cette exécution, défaut 0 |
| `human_seconds` | Temps humain imputé, défaut 0 |
| `human_rate_minor` | Valeur d’une heure humaine dans la devise du projet, défaut 0 |
| `input_tokens`, `output_tokens` | Mesures facultatives ; `null` si non observées |
| `model`, `actor`, `purpose`, `outcome` | Attribution et résultat de l’exécution |
| `summary`, `next_step` | Journal de transmission obligatoire |

Les valeurs d’infrastructure et de temps humain à zéro signifient **non imputées**. Renseigner
ces champs pour obtenir un coût économique complet ; le framework ne les mesure pas tout seul.
L’indicateur `complete` signifie que les montants LLM sont renseignés pour les exécutions enregistrées,
pas qu’une facture a été réconciliée ni qu’aucune activité n’a été oubliée.

## Formules

Pour une exécution :

```text
coût humain = arrondi au centime, demi vers le haut(secondes × tarif horaire / 3 600)
coût connu du run = coût LLM connu + infrastructure imputée + coût humain imputé
coût connu d’une tâche = somme de tous ses runs
```

Pour le portefeuille du projet, sans filtre temporel dans la v0.1 :

```text
coût / tâche exécutée = coût de tous les runs / nombre de tâches ayant au moins un run
coût / tâche acceptée = coût de tous les runs / nombre de tâches acceptées
coût / livrable accepté = coût de tous les runs / nombre de livrables des tâches acceptées
```

**Les échecs et les tâches annulées restent au numérateur des ratios du portefeuille.** Le ratio
par tâche affiché sur sa propre ligne utilise seulement les coûts de cette tâche. Les deux mesures
ont des usages différents et ne doivent pas être comparées comme si elles étaient identiques.

Exemple fictif : tâche A acceptée, deux livrables, coût 20 EUR ; tâche B abandonnée, coût 10 EUR.
Le portefeuille coûte 30 EUR : 15 EUR par tâche exécutée, 30 EUR par tâche acceptée et 15 EUR
par livrable accepté. La ligne A seule affiche 10 EUR par livrable accepté.

## Absences, estimations et abonnements

Un dénominateur nul donne `null`, affiché « Non calculable ». Un coût LLM inconnu rend les ratios
globaux incomplets ; le coût connu reste visible, sans prétendre être le total final. Les tâches
sans exécution ne sont pas des tâches exécutées. Un coût renseigné à zéro peut être réel ; il doit
être justifié par `cost_note`.

Pour un abonnement : définir une période, un montant et une clé d’allocation (par exemple minutes
actives ou poids de consommation). Consigner cette méthode et utiliser `estimate`. Ne pas additionner
une allocation d’abonnement et une facture API correspondant à la même consommation. Aucun tarif de
modèle n’est embarqué : il vieillirait et ne couvrirait pas les contrats particuliers.

Les ratios calculés avec des estimations sont affichés comme tels. Un nombre de tokens ne suffit
pas à deviner un prix (cache, niveaux de service, crédits et contrats peuvent changer le calcul).

## Budgets

`budget_minor` et `max_runs` appartiennent au contrat de tâche. `task start` compare les coûts déjà
enregistrés et le nombre de runs aux plafonds. Une nouvelle tentative doit rappeler cette commande.
Les revues et la coordination comptent aussi dans `max_runs` : prévoir leur coût dès le cadrage.

`run record` accepte un dépassement après exécution : refuser son enregistrement masquerait le
coût réel. `check` et la carte signalent le dépassement. Des coûts inconnus ne permettent pas un
contrôle financier strict. Le contrôleur 0.2 surveille les délais et réserve les places d’appels simultanés, mais le prix
d’un appel en cours n’est pas borné : ajouter une limite fournisseur pour un plafond effectif.

## Corrections et historique

La CLI crée les runs sans écrasement et ne propose pas de suppression. Pour corriger une erreur
comptable, modifier le run dans une PR explicite avec justification et revue ; Git conserve le diff.
Ne pas créer un deuxième run pour remplacer la facture du premier : cela doublerait la dépense.
La v0.1 ne dispose pas encore d’un journal comptable d’ajustements signé.

L’acceptation d’une tâche compte tous ses livrables une fois. Après régression, ouvrir une nouvelle
tâche/finding lié ; le coût des réparations entre au portefeuille. La révocation et les cohortes de
livraison sont des évolutions possibles, pas des capacités promises dans cette version.

## Attribution de l’orchestration

Chaque appel reçoit `orchestration`, `role`, `work_item`, `requested_model`, `observed_models`,
`identity_status` et `identity_source`. `costs` ajoute les groupes `by_role` et `by_orchestration`.
Les appels de planification, revue et arbitrage comptent dans le budget de la même tâche et dans
le coût de ses livrables. Un modèle inattendu peut avoir coûté : son montant déclaré reste conservé.
Un timeout, arrêt ou échec de transport sans réponse exploitable reste de coût inconnu.
