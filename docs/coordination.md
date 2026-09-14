# Interfaces et points de contrôle entre agents

Un worktree est une copie isolée. Ses JSON ne sont pas une mémoire partagée en direct.
Le contrôleur transmet désormais un instantané de coordination à chaque travailleur : plan complet,
interfaces figées, travaux intégrés, comptes rendus précédents et décisions des points de contrôle.
Deux travailleurs du même lot partent du même instantané. Le lot suivant reçoit l'état actualisé.

## Définir une interface avant de déléguer

Un contrat précise les signatures, unités, formats, erreurs et invariants partagés. Il peut couvrir
une API, un schéma SQL, un événement ou une convention métier. Il ne donne aucun droit d'écriture
supplémentaire. Enregistrer un fichier JSON, par exemple `prix-v1.json` :

```json
{
  "id": "I-prix-v1",
  "created_at": "2026-09-14T08:00:00+00:00",
  "name": "prix",
  "version": 1,
  "paths": ["src/pricing", "src/dashboard"],
  "specification": "GET /prices renvoie {amount_minor: integer, currency: string}. amount_minor est en centimes EUR, jamais en euros décimaux. Valeurs négatives interdites. Absence de prix : HTTP 404, jamais montant zéro.",
  "checks": ["tests"],
  "supersedes": null
}
```

`checks` référence des commandes déjà configurées dans la politique ; remplacer `tests` par le
nom réel de votre contrôle. Ces commandes s'exécutent lors de la vérification finale du candidat.
Le point de contrôle intermédiaire est une inspection par l'orchestrateur, pas une suite de tests
supplémentaire exécutée automatiquement à chaque lot. Un tableau vide est permis pour une convention
sans test automatisé, mais la couverture est alors seulement déclarative et soumise à la revue.

```bash
framework schema interfaces
framework import interfaces prix-v1.json
framework task create --title "Livrer le dashboard de prix" --owner pilote \
  --scope src/pricing --scope src/dashboard \
  --interface I-prix-v1 \
  --criterion "Le dashboard affiche le prix et la devise sans erreur d’unité" \
  --deliverable "Dashboard de prix fonctionnel" --budget-minor 15000 --max-runs 20
framework context src/dashboard
```

Le contrat importé est conservé dans `.framework/interfaces/I-prix-v1.json`. La tâche référence
cet identifiant et réserve automatiquement la ressource `interface:prix` entre tâches du même clone.
Deux tâches utilisant cette interface sont donc sérialisées par leur bail ; les travailleurs d'une
même tâche peuvent rester parallèles si leurs chemins et dépendances le permettent.

Une version 2 utilise un nouvel identifiant, `version: 2`, le même `name` et
`supersedes: "I-prix-v1"`. L'import refuse une version dupliquée, une chaîne rompue et un contrôle
inconnu. On conserve la version 1. Mettre ensuite à jour les références de la tâche dans une révision
explicite de son contrat ; le moteur ne l'amende jamais pour se débloquer. Committer les interfaces,
le contrat de tâche et le code avant le lancement. La CLI d'import ne remplace pas un fichier existant.
Git et les protections de revue restent nécessaires pour contrôler les éditions directes.

## Transmission et arrêt en cas de divergence

1. Le contrôleur fige les interfaces dans la session `O-…`. Leur contenu participe aussi à l'empreinte
   du code ; une modification après vérification rend la preuve obsolète.
2. Chaque travailleur reçoit toutes les interfaces épinglées de la tâche, avec des références
   `I-…@version:empreinte`, ainsi que le plan et les comptes rendus déjà intégrés.
3. Sa réponse contient `summary`, `acknowledged_interfaces` et `change_requests`.
   Toutes les références doivent être reproduites exactement. Une omission ou une ancienne empreinte
   bloque le lot et reste enregistrée comme appel échoué, avec son coût disponible.
4. S'il faut modifier une unité, une signature ou un schéma, le travailleur renseigne `change_requests`
   et s'arrête. Le contrôleur conserve la demande, attend les autres appels déjà engagés et bloque
   avant d'intégrer le lot. Il ne lance pas les dépendants.
5. Après intégration d'un lot sans demande de changement, le modèle choisi pour `orchestrator`
   inspecte le diff du lot, le candidat, les contrats et les comptes rendus. Sa réponse au point
   de contrôle doit être `continue` ou `block`, avec reconnaissance exacte des interfaces.
6. Seul `continue` permet le prochain lot. Un blocage nécessite une correction du cadrage ou une
   révision de contrat puis un nouveau lancement depuis la base commitée. Il n'y a pas de reprise
   automatique d'un candidat partiellement bloqué.
7. Après le dernier point de contrôle, les tests configurés puis la revue indépendante gardent
   leur rôle. Le passage des points de contrôle est aussi vérifié avant l'intégration explicite.

Une tâche sans interface déclarée utilise une liste vide ; les points de contrôle restent obligatoires.
Le framework ne découvre pas automatiquement les interfaces oubliées. La qualité du cadrage et des
tests demeure déterminante. Reconnaître une empreinte prouve une réponse conforme au protocole,
pas la compréhension du modèle ni l'absence de bug.

## Ce que voit le pilote

`framework orchestration show O-IDENTIFIANT` expose `interfaces`, `plans`, `handoffs` et
`checkpoints`, en plus des appels et de leurs coûts. Chaque compte rendu indique le tour, le travail
et le commit du travailleur lorsqu'il existe. Les points de contrôle sont reliés à leur appel `R-…`.
La carte HTML présente une vue Interfaces et les fiches complètes des sessions.

Les checkpoints utilisent le modèle choisi par l'utilisateur pour l'orchestrateur. Ils consomment
le budget et les places de `max_runs` : prévoir **un appel supplémentaire par lot**, y compris le
lot final et les lots de correction. Pour deux travailleurs parallèles puis un travail dépendant,
un tour réussi compte 1 plan + 3 travailleurs + 2 points de contrôle + 1 revue = **7 appels**.

## Mode accompagné et compatibilité

Les agents Codex, Claude, Cursor, Gemini ou autres peuvent lire les mêmes JSON via `context`.
En mode accompagné, le pilote transmet explicitement les comptes rendus et organise les contrôles
intermédiaires ; le fichier HTML ne lance rien. Le mécanisme bloquant décrit ci-dessus est celui du
contrôleur `orchestration run`, pas une surveillance permanente de toutes les sessions de l'éditeur.

Le pont de commande passe à `protocol_version: 2`. Respecter `response_schema` à chaque appel :
une requête `role: orchestrator` avec `payload.phase: checkpoint` attend le verdict du point de
contrôle, et non un nouveau plan. La réponse du travailleur exige les deux tableaux, même vides.
Les anciens ponts doivent être adaptés. Les anciennes fiches restent lisibles ; leurs sessions
n'acquièrent pas rétroactivement des points de contrôle qui n'ont jamais eu lieu.
