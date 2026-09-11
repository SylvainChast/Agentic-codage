# Une mission de bout en bout

## Préparer le projet

Installer la CLI, lancer `framework init`, puis remplacer le contrôle d’amorçage par les vrais
contrôles du produit. Commiter cette configuration et les adaptateurs. Pour le framework lui-même,
utiliser `python3 bin/framework` à la place de `framework` si la commande n’est pas installée.

Le coordinateur découpe le besoin selon des résultats testables et des interfaces stables. Une tâche
peut livrer plusieurs éléments, mais son acceptation est globale. Pour accepter séparément deux
éléments, créer deux tâches. Commencer avec au plus deux réservations simultanées ; la politique
`max_active_tasks` permet d’ajuster cette limite. Aucun modèle n’est lancé automatiquement.

## Déclarer et réserver

```bash
framework task create --title "Calculer le total TTC" --owner agent-a \
  --scope src/pricing.py --scope tests/test_pricing.py --resource api:pricing \
  --criterion "Le total de 100 à 20 pour cent vaut 120" \
  --criterion "Un montant négatif est refusé" \
  --deliverable "Calcul TTC avec validation" --budget-minor 2500 --max-runs 5
```

Conserver l’identifiant `T-…` renvoyé. Les options répétables ajoutent un chemin, une interface,
un critère, une décision ou une dépendance. Les chemins sont littéraux, sans glob : `src/billing`
couvre ce répertoire et ses descendants, mais pas `src/billing-old`.

Dans un flux protégé, faire intégrer cette déclaration dans une **PR de cadrage** avant le code.
`framework check --base SHA --task T-…` exige ce contrat sur la base de confiance ; une PR de code
ne peut pas élargir elle-même son autorisation en modifiant son propre contrat.

```bash
git worktree add -b codex/pricing ../projet-pricing main
cd ../projet-pricing
framework lease acquire T-IDENTIFIANT --owner agent-a --ttl 3600
framework task start T-IDENTIFIANT --actor agent-a
```

Les réservations sont partagées par les worktrees d’un même clone. Elles expirent ; la même
commande les renouvelle. Réserver également les contrats tels que `api:pricing` ou `db:migrations`
pour coordonner des fichiers différents qui modifient le même comportement. Un bail ne remplace
ni des tests d’intégration ni l’isolation de l’environnement d’exécution.

## Implémenter et enregistrer chaque tentative

Lire `framework context src/pricing.py`. Implémenter seulement le contrat courant. Avant toute
nouvelle tentative, rappeler `task start` : la commande refuse un budget enregistré épuisé ou
un nombre maximal d’exécutions atteint. Elle n’interrompt pas un modèle en cours de génération.

```bash
framework run record T-IDENTIFIANT --actor agent-a --model "nom-observe" \
  --purpose implementation --outcome failed --cost-source estimate --llm-cost-minor 80 \
  --cost-note "Allocation estimée de l’abonnement selon les minutes actives" \
  --summary "Le test du montant négatif échoue ; cas reproduit" \
  --next-step "Corriger la validation puis relancer les contrôles"
```

Une réussite ultérieure donne lieu à un **autre run**. Ne pas réécrire l’échec. Un journal conserve
les faits utiles, les conclusions et la suite ; il ne doit contenir ni secrets ni raisonnement privé.
Les exécutions de revue et coordination utilisent `--purpose review` ou `coordination`. Un coût
inconnu se note avec `--cost-source unknown`, sans `--llm-cost-minor`.

## Produire une preuve

```bash
framework check
framework verify T-IDENTIFIANT
framework task submit T-IDENTIFIANT --actor agent-a
```

`verify` exécute les commandes de la politique dans la racine du projet, sans shell. Un échec,
un dépassement du délai ou une modification du code par les contrôles produit une preuve en
échec. Les fichiers sont conservés dans `.framework/evidence/` : un JSON et un log par contrôle.
Le JSON lie les résultats à une empreinte du candidat et du contrat de tâche.

Après modification du code, de la politique ou d’une décision, recommencer la vérification. Le
commit observé est une aide de navigation ; l’empreinte du contenu est le critère de fraîcheur.

## Faire relire et accepter

Un acteur qui n’a pas implémenté la tâche inspecte le diff, les décisions, les tests et les critères.
Changer seulement de nom ou de modèle ne crée pas une indépendance réelle. L’identité stockée
est déclarative ; une plateforme de revue authentifiée doit assurer cette séparation en production.

```bash
framework review record T-IDENTIFIANT --reviewer reviewer-b --verdict approve \
  --evidence E-IDENTIFIANT --criterion "Le total de 100 à 20 pour cent vaut 120" \
  --criterion "Un montant négatif est refusé" \
  --summary "Diff et cas limites examinés ; critères couverts par les tests indiqués"
framework task accept T-IDENTIFIANT --review V-IDENTIFIANT --actor maintainer
framework map
```

Ces commandes sont à exécuter **après une vraie revue**, avec son résultat. Elles ne réalisent pas
la revue humaine/agentique à sa place. L’acceptation libère le bail mais ne fusionne ni ne déploie.
La personne ou le coordinateur qui accepte doit disposer de l’autorité déjà donnée par l’utilisateur.

Pour une reprise : `request_changes`, puis `task start`, correction, nouveau run, nouvelle preuve
et nouvelle revue. La v0.1 exige une preuve passée pour enregistrer une revue structurée, même
`request_changes` ; en cas de tests en échec, conserver le diagnostic dans un finding ou un run.

## Conflit, interruption et annulation

- Conflit textuel : résoudre dans le périmètre réservé et revérifier le candidat complet.
- Conflit de conception : un tiers compare les options au contrat ; proposer une décision distincte.
- Dépendance instable : ne pas lancer le consommateur avant acceptation du fournisseur.
- Budget épuisé : enregistrer le dépassement réel, puis réviser le contrat avant de reprendre.
- Abandon : `framework task cancel TASK --actor OWNER` conserve les coûts et libère le bail.
- Session perdue : laisser expirer le bail ; la prochaine session consulte la tâche et les runs.

Le verrou ne traverse pas plusieurs clones ni machines. Le coordinateur doit utiliser un clone
commun pour la v0.1, ou un service de réservation externe avant un déploiement distribué.
