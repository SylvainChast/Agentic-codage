# Qualité et préparation d’une due diligence technique

L’objectif est une ingénierie examinable : un tiers doit retrouver les décisions, les risques,
les contrôles exécutés et l’origine des livraisons. « Grade A » n’est pas une certification fournie
par ce dépôt. Le [NIST SSDF](https://csrc.nist.gov/projects/ssdf) structure les pratiques de développement
sécurisé ; [SLSA](https://slsa.dev/spec/v1.2/) structure la sécurité de la chaîne de livraison et sa
provenance. Ces références guident la démarche sans revendiquer un niveau de conformité.

## Ce que le socle vérifie

| Contrôle | Implémentation v0.1 |
|---|---|
| Contrats structurés | Schémas stricts et références entre tâches/décisions |
| Concurrence de travail | Réservation atomique locale des chemins et interfaces |
| Périmètre | Diff contre un contrat présent sur une base de confiance, option `--base --task` |
| Transmission | Journal et coût requis avant soumission et acceptation |
| Preuves courantes | Empreinte des fichiers et du contrat, logs avec hash, commandes et codes de sortie |
| Revue distincte | Identité déclarée différente des implémenteurs, tous les critères renseignés |
| Dette temporaire | Exceptions expirées ou rattachées à un finding résolu rejetées |
| Coûts honnêtes | Absences, estimations, échecs et dépassements visibles |
| Taille de code | Plafond configurable sur les fichiers Python sous `src/` |
| Instructions partagées | Détection de la divergence des adaptateurs |

Le plafond de taille est un contrôle simple de cette première version, pas une mesure de complexité.
Pour une autre stack, ajouter une analyse adaptée. Les références aux décisions n’établissent pas la
conformité du comportement : leur associer des tests d’architecture ou d’intégration.

## Ce qu’un produit doit ajouter

| Domaine | Exigence et preuve attendue |
|---|---|
| Fonctionnel | Tests de parcours, erreurs, limites, compatibilité et contrats publics |
| Architecture | Frontières explicites, dépendances contrôlées, décisions motivées |
| Sécurité | Modèle de menace, isolation, authentification/autorisation testées, scans, traitement des findings |
| Dépendances | Verrouillage, inventaire/SBOM, licences, vulnérabilités et provenance |
| Construction | Environnement contrôlé, artefacts identifiables, intégrité et provenance vérifiable |
| Données | Migrations testées, restauration validée, droits d’accès et gestion du cycle de vie |
| Exploitation | Logs sans secrets, métriques, alertes, procédures d’incident et de retour arrière |
| Produit | Performance, accessibilité, comportements UX et critères métier vérifiés |
| Transmission | Installation reproductible, propriétaires, dette, limites et calendrier de traitement |

Ajouter les commandes pertinentes dans la politique **et dans une CI protégée**. Une commande qui
ne teste rien ne devient pas une preuve utile parce qu’elle retourne zéro. Les contrôles sensibles
et les critères ne doivent pas être modifiés par l’implémenteur sans revue dédiée.

## Contrôles bloquants et risque

Le socle bloque les incohérences structurelles. Un finding ouvert n’empêche pas automatiquement
l’acceptation : sa sévérité doit être reliée à une politique métier de livraison dans le profil du
produit. Cette politique doit notamment décider du traitement des vulnérabilités critiques/élevées,
des exceptions et de l’autorité habilitée à accepter un risque. La v0.1 ne fournit pas de dérogation
exécutable universelle.

Une revue locale est une déclaration. Configurer de vraies revues authentifiées, des droits de
branche et des identités de CI indépendantes pour empêcher l’auto-approbation. Les logs locaux sont
hashés pour détecter les altérations accidentelles, pas signés contre un acteur qui contrôle le dépôt.

## Dossier de preuves

Conserver les contrats, décisions et findings dans Git ; les résultats et liens d’artefacts de CI
sur la plateforme. Le HTML sert à naviguer dans les fiches. Pour une livraison à auditer, conserver
le commit, l’environnement de construction, l’inventaire de dépendances, les rapports CI, les revues
et la procédure de restauration. Les tests du framework valident son mécanisme ; ils ne certifient
pas la sécurité des applications qui l’utilisent.
