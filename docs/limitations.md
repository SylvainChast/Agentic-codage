# Périmètre de la version 0.1

## Disponible

CLI portable, initialisation, adaptateurs et deux skills, contrats de tâches, réservations
atomiques entre worktrees, journaux et coûts, vérifications exécutées, revues déclarées, acceptation
sur preuve courante, extraction de contexte, schémas stricts et carte HTML autonome.

## Limites explicites

- **Pas d’orchestrateur de modèles** : aucun lancement automatique, routage de modèles, abonnement,
  MCP ou gestion de clés. Les agents existants appellent la CLI.
- **Pas de coordination multi-machine** : les baux concernent les worktrees d’un seul clone local.
- **Pas de blocage physique des écritures** : les baux sont coopératifs et les identités déclaratives.
  Un acteur ayant accès au disque peut modifier les fichiers. La CI et les droits complètent le socle.
- **Pas de limite fournisseur de dépenses** : le budget empêche un nouveau `task start` sur les montants
  enregistrés ; il ne coupe pas une génération ni ne détecte les exécutions oubliées.
- **Pas de certification Grade A** : ni un nombre de tests ni un indicateur vert ne remplace une revue,
  un profil de sécurité du produit et des preuves d’exploitation.
- **Pas de scan de sécurité universel** : les scanners de secrets, dépendances, licences, AST,
  complexité et architecture doivent être choisis et ajoutés pour la stack.
- **Pas de code-map AST automatique** : les liens proviennent des scopes, chemins et décisions.
- **Pas de vérification sémantique des décisions par simple référence** : associer des tests au choix.
- **Pas de vérification de chargement dans tous les éditeurs** : les adaptateurs sont générés et contrôlés,
  mais chaque hôte doit être configuré et essayé avec sa version.
- **Pas de budget distribué ou comptabilité certifiée** : coûts saisis/importés manuellement, une devise
  à deux décimales, pas de synchronisation de factures, de cohortes ni d’ajustements comptables signés.
- **Pas d’acceptation partielle ou révocation automatique** : une tâche accepte son ensemble de livrables.
- **Pas d’historique complet du runtime** : conserver séparément les artefacts CI et attestations de build.
- **Pas de hooks de permission universels** : les mécanismes des éditeurs diffèrent ; le socle reste la CLI.
- **Pas de licence open source choisie** : décider avant une redistribution publique.

## Évolutions à évaluer avec des mesures

Une prochaine version peut ajouter : intégration automatique aux PR avec contrats issus d’une base
protégée, réservation centralisée multi-machine, identités authentifiées, collecteurs de facturation,
profils de stack, graphe AST, snapshots d’artefacts CI et attestations de provenance.

Chaque ajout doit résoudre une attente ou un risque constaté. Mesurer d’abord le coût par livraison
acceptée, le temps de revue et les reprises ; ne pas augmenter le nombre d’agents pour lui-même.
