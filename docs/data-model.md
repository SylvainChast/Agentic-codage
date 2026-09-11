# Modèle de données

Les schémas exacts sont dans `src/agentic_codage/assets/schemas/`. La commande
`framework schema tasks` (ou `runs`, `decisions`, `findings`, `exceptions`, `evidence`, `reviews`,
`policy`) imprime le schéma. Version du format : `policy.schema_version = 1`.

Le validateur interne implémente uniquement les mots-clés utilisés par ces schémas : `type`,
`properties`, `required`, `additionalProperties`, `enum`, `items`, `minItems`, `uniqueItems`,
`minLength`, `pattern`, `minimum`. Il n’est pas une implémentation générale de JSON Schema.
Les clés dupliquées, nombres non finis, champs inconnus, types incorrects et chemins non littéraux
sont rejetés. Les dates de création et d’expiration nécessitent un fuseau.

| Entité | Clé | Rôle et relations |
|---|---|---|
| Tâche | `T-…` | Contrat, propriétaire, chemins, ressources, critères, livrables, décisions et dépendances |
| Run | `R-…` | Une exécution et son coût, journal, modèle et tâche |
| Décision | `D-…` | Contexte, choix, alternatives, propriétaire, chemins et noms de contrôles |
| Finding | `F-…` | Risque reproductible, sévérité, propriétaire, chemins, état et résolution |
| Exception | `X-…` | Justification temporaire rattachée à un finding ouvert, propriétaire et échéance |
| Preuve | `E-…` | Empreinte, contrat, commandes exécutées, codes de sortie et hashes des logs |
| Revue | `V-…` | Verdict, critères, identité déclarée, empreinte et preuve examinée |

## Transitions

```text
planned → active → submitted → accepted
             ↑         │
             └─────────┘  reprise après revue, avec budget restant
planned / active / submitted → cancelled
```

Le contrat d’une tâche acceptée est figé ; sa modification est détectée. Les nouveaux runs peuvent
être enregistrés après acceptation pour ne pas masquer des coûts connus tardivement. Les revues
historiques restent conservées même quand leur ancien contrat n’est plus celui de la tâche courante.
Une tâche acceptée conserve le contrat et l’empreinte exacts de sa revue et de sa preuve.

## Exemple de décision

```json
{
  "id": "D-api-boundary",
  "created_at": "2026-09-11T12:00:00+00:00",
  "title": "Stabiliser le contrat de facturation",
  "context": "Plusieurs composants consomment le calcul du total.",
  "decision": "Le calcul est pur et refuse les montants négatifs.",
  "alternatives": ["Calcul dupliqué dans chaque interface"],
  "owner": "maintainer",
  "status": "proposed",
  "superseded_by": null,
  "paths": ["src/billing"],
  "checks": ["tests"]
}
```

Importer avec `framework import decisions /chemin/decision.json`. Le nom de contrôle doit exister
dans la politique. L’import valide la forme ; `framework check` vérifie les relations entre fiches.
Promouvoir une décision à `active` dans une modification revue par son propriétaire. Les tâches
actives ne référencent que des décisions actives. Une décision remplacée pointe vers son successeur
actif. Les références historiques des tâches terminées sont conservées.

## Exceptions

Une exception n’est jamais un bouton pour ignorer la CI. La v0.1 vérifie son propriétaire déclaré,
son lien vers un finding ouvert et sa date d’expiration. L’exception expirée ou liée à un finding
résolu bloque la validation jusqu’à son traitement. Les mécanismes de dérogation propres à la stack
nécessitent une implémentation et une revue spécifiques ; aucun contournement générique n’est fourni.

## Modifier une fiche

Créer les tâches, runs, preuves et revues par la CLI. Les décisions, findings et exceptions peuvent
être importés ou édités en JSON dans une PR. Les changements de critères, de propriétaire, de budget
ou de périmètre demandent une nouvelle révision du contrat avant une PR d’implémentation protégée.
La CLI n’authentifie pas le rôle du signataire ; les droits Git et les revues assurent cette autorité.
