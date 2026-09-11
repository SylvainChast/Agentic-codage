# Référence CLI

Toutes les commandes acceptent `framework --root CHEMIN ...`. Cette option globale se place avant
la sous-commande. Le lancement depuis les sources est `python3 bin/framework ...`. La sortie est
du JSON UTF-8 ; `--help` donne les options exactes. Pas de service d’arrière-plan.

| Commande | Effet |
|---|---|
| `init --name NOM [--currency EUR]` | Crée politique, mémoire, guide et adaptateurs sans écraser les consignes |
| `adapters [--check]` | Crée les adaptateurs manquants ; détecte toute divergence sans écrasement |
| `schema KIND` | Affiche le JSON Schema embarqué |
| `import KIND FICHIER` | Ajoute une décision, un finding ou une exception validé |
| `task create …` | Crée un contrat `planned` avec un identifiant unique |
| `task list` / `task show TASK` | Lit les contrats |
| `task start TASK --actor OWNER` | Démarre/reprend après contrôle du bail, des dépendances et des budgets |
| `task submit TASK --actor OWNER` | Passe en revue, avec bail et au moins un journal de coût |
| `task cancel TASK --actor OWNER` | Annule sans effacer les coûts et libère le bail |
| `task accept TASK --review REVIEW --actor ACTOR` | Enregistre l’acceptation et libère le bail |
| `lease acquire TASK --owner OWNER [--ttl 3600]` | Réserve ou renouvelle, maximum 86 400 secondes |
| `lease release TASK --owner OWNER` | Libère le bail ; seul le propriétaire déclaré peut le faire |
| `lease list` | Affiche les réservations actives du clone |
| `run record TASK …` | Ajoute un journal d’exécution et sa mesure de coût |
| `verify TASK` | Exécute les commandes de la politique et conserve les résultats |
| `review record TASK …` | Enregistre un verdict sur une preuve courante et les critères exacts |
| `check [--base SHA --task TASK]` | Valide les fiches ; optionnellement le périmètre du diff |
| `context CHEMIN` | Retourne décisions actives, risques, tâches et transmissions concernés |
| `costs` | Retourne coûts des tâches et ratios du portefeuille |
| `map [--check]` | Génère la carte HTML ou vérifie la fraîcheur de ses données |

## Codes de retour

- `0` : commande exécutée, contrôle réussi le cas échéant.
- `1` : validation ou vérification exécutée mais en échec.
- `2` : arguments incorrects, fichier invalide, transition interdite, preuve périmée ou erreur opérationnelle.

Les erreurs métier sont en JSON sur stderr ; argparse affiche ses erreurs d’utilisation habituelles.
Une commande interrompue par le système suit les codes de retour du système. Les logs des tests ne sont
pas mélangés avec le JSON de la CLI : ils sont écrits dans `.framework/evidence/`.

## Résolution des erreurs fréquentes

| Erreur | Action |
|---|---|
| Contrôle `configure-project-checks` en échec | Installer de vrais contrôles dans la politique |
| Bail absent ou périmètre modifié | Acquérir/renouveler le bail correspondant au contrat |
| Périmètre réservé par une autre tâche | Attendre/libérer la tâche légitime ou redécouper le travail |
| Budget épuisé | Enregistrer les coûts réels puis faire réviser le contrat |
| Evidence stale | Revérifier le contenu courant et obtenir une nouvelle revue |
| Auto-revue | Faire intervenir un acteur réellement indépendant |
| Carte périmée | Régénérer après la dernière modification des sources/fiches |
| Adapter drift | Réconcilier la source canonique et le fichier concerné explicitement |
| Contrat absent de la base | Intégrer la PR de cadrage avant la PR d’implémentation |

Aucune commande ne choisit de modèle, n’ouvre une PR, ne fusionne une branche ou ne déploie un produit.

## Orchestration (0.2)

`framework orchestration` expose `init`, `set-role`, `config`, `doctor`, `run`, `list`, `show`,
`feedback`, `cancel` et `integrate`. Le [guide détaillé](orchestration.md) décrit arguments,
protocole, coûts et états. `run` retourne 0 pour ready, 1 pour une session bloquée/annulée ;
les erreurs de configuration ou préconditions retournent 2.
