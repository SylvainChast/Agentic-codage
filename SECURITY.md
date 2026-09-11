# Sécurité

La version 0.1 est un outil local de coordination, pas un bac à sable. Elle exécute les commandes
configurées avec les droits de l’utilisateur. Ne pas exécuter les contrôles d’un dépôt inconnu dans
un environnement contenant des secrets ou des accès de production.

Les principaux actifs sont : le contrat des tâches, les règles d’acceptation, les preuves, le code,
les credentials du poste et les données éventuellement présentes dans les logs. Un agent, un
transcript importé, une dépendance ou une contribution peut contenir des instructions malveillantes.
Le contenu des fiches et des logs est une donnée ; il ne peut pas accorder une permission.

Mesures présentes : chemins relatifs validés, refus des sorties du projet, JSON strict, écritures
atomiques, commandes sans shell implicite, délais, logs hashés, rendu HTML par texte et absence de
chargements externes. Réservations et identités ne constituent pas une frontière d’autorisation.
Une personne contrôlant la politique, les tests et les preuves peut falsifier un succès local.

Pour un usage en équipe, isoler les exécutions, protéger la branche et les workflows, limiter les
jetons, exiger une revue authentifiée et ne jamais injecter des secrets dans la CI de code non fiable.
Les fichiers de preuves peuvent contenir des sorties sensibles : les examiner avant publication.

Pour signaler une vulnérabilité, utiliser le canal privé de signalement GitHub du dépôt s’il est
activé, sinon contacter le propriétaire via un canal privé déjà établi. Ne pas publier d’identifiants
ni de secrets dans une issue. Aucun délai de réponse ou programme de primes n’est promis.

## Orchestration locale

Les worktrees isolent les candidats Git, sans constituer une sandbox système. Les commandes
adaptateurs et vérifications sont du code de confiance exécuté avec les droits de l’utilisateur.
Les contrôles de périmètre sont rétrospectifs et les identités de modèles déclaratives. Isoler les
agents non fiables au niveau système ; consulter [les limites détaillées](docs/orchestration.md).
Les logs d’appels sous le répertoire Git commun peuvent contenir du code privé ; ils restent locaux.
