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
| `costs [--task TASK]` | Coûts du portefeuille ou d’une livraison, ventilés par rôle, modèle, session et étape |
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

## Méthode produit et développement

| Commande | Effet |
| --- | --- |
| `method catalog` | Liste les parcours et étapes disponibles |
| `method init TASK --track express\|feature\|product [--ui]` | Active le cadrage adapté sur une tâche existante |
| `method template prd\|stories` | Renvoie gabarit Markdown et schéma JSON versionné |
| `method scaffold TASK --kind prd\|stories --file CHEMIN.md` | Crée une copie à remplir dans le périmètre réservé, sans écrasement |
| `method story TASK --id STORY --complexity N --note TEXTE` | Sélectionne une story, sa taille de 1 à 5 et ses notes ; `--note` répétable |
| `method prompt ETAPE --task TASK [--max-chars 12000]` | Charge une procédure et ses extraits de contexte pertinents |
| `method record TASK --kind TYPE --file CHEMIN.md --author ACTOR [--input A-ID]` | Enregistre une révision de document et ses entrées ; `--input` répétable |
| `method use TASK A-ID` | Réutilise et sélectionne un document déjà enregistré |
| `method review TASK --artifact A-ID --reviewer ACTOR --verdict approve\|request_changes --summary TEXTE [--finding TEXTE]` | Enregistre une revue réelle de cadrage ; `--finding` répétable |
| `method status TASK` | Décrit les documents et blocages, sans lancer d’agent |
| `method gate TASK` | Refuse de poursuivre si la préparation est incomplète ou périmée |
| `method ship TASK --base SHA --review V-ID` | Prépare localement le corps d’une PR à partir d’une implémentation revue |

`run record --stage ETAPE` attribue une exécution à une étape sans en modifier le coût total.
`method` ne lance pas de fournisseur : les skills exécutent les procédures dans l’hôte courant,
et `orchestration run` reste le mécanisme de délégation configurée. Voir les
[exemples complets et formats](methodologie.md).

## Profils d'architecture

- `method starters` : catalogue public avec provenance, licence et limites déclarées.
- `method architecture TASK --boilerplate PROFIL [--revision SHA] [--constraint TEXTE]` : choix de base MIT.
- `method architecture TASK --custom --stack TEXTE [--constraint TEXTE]` : stack libre.
- `method architecture TASK --existing [--stack TEXTE] [--constraint TEXTE]` : conservation du projet existant.

Les trois modes sont exclusifs. `--stack` et `--constraint` sont répétables. La sélection remplace
la précédente et transmet le contexte aux agents, sans clonage ni installation.
Voir [le parcours et l'épinglage de révision](boilerplates.md).
