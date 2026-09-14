# Architecture : bases SaaS libres et choix utilisateur

Le framework propose des profils publics pour éviter de recommencer le même cadrage à chaque SaaS.
L'utilisateur choisit une base, définit sa propre stack ou conserve un projet existant. Aucun profil
n'est imposé. Cette couche sélectionne et documente le socle ; elle ne crée pas encore une application,
ne clone pas de code et n'installe aucune dépendance.

## Catalogue initial

Documentation publique et licences consultées le 14 septembre 2026. Les capacités ci-dessous sont
celles annoncées par les projets, pas le résultat d'un audit de leur code par Agentic Codage.

| Profil | Stack et contenu annoncé | À examiner avant adoption |
| --- | --- | --- |
| `nextjs-saas` | Next.js, TypeScript, PostgreSQL, Drizzle, shadcn/ui ; authentification, équipes, abonnements Stripe, dashboard | Base volontairement minimale et pédagogique ; compléter les contrôles adaptés au produit |
| `open-saas` | Wasp, React, Node.js, Prisma ; authentification, paiements, emails, tâches de fond, exemples Playwright | Accepter les conventions et le compilateur Wasp ; sélectionner seulement les services utiles |
| `fastapi-react` | FastAPI/Python, React/TypeScript, SQLModel, PostgreSQL ; authentification, client API généré, Docker, tests et CI | Socle d'application généraliste ; préciser la facturation et les règles SaaS propres aux organisations |

Sources : [Next.js SaaS Starter](https://github.com/nextjs/saas-starter),
[Open SaaS](https://github.com/wasp-lang/open-saas),
[Full Stack FastAPI Template](https://github.com/fastapi/full-stack-fastapi-template).
Leurs licences de code sont MIT : [Next.js](https://github.com/nextjs/saas-starter/blob/main/LICENSE),
[Open SaaS](https://github.com/wasp-lang/open-saas/blob/main/LICENSE),
[FastAPI](https://github.com/fastapi/full-stack-fastapi-template/blob/master/LICENSE).
Conserver les notices d'origine lors d'une reprise. Une licence de code gratuite ne rend pas gratuits
l'hébergement, les services externes ou les appels aux modèles.

## Choisir avec l'agent ou la CLI

Le skill d'architecture accepte ces intentions dans les hôtes à commandes slash :

```text
/architecture --boilerplate nextjs-saas
/architecture --boilerplate open-saas
/architecture --boilerplate fastapi-react
/architecture --custom "Django, PostgreSQL, hébergement interne"
/architecture --existing
```

Dans Codex, utiliser `$swarm-architecture` avec la même demande. Ces arguments sont interprétés par
le skill ; ils ne constituent pas un parseur universel dans les IDE. L'agent identifie la tâche,
respecte le choix utilisateur et utilise les commandes portables ci-dessous.

Après création d'une tâche et `method init`, consulter les profils puis sélectionner le socle :

```bash
framework method starters
framework method architecture T-IDENTIFIANT --boilerplate nextjs-saas \
  --constraint "Les données de chaque organisation restent isolées"
framework method prompt architecture --task T-IDENTIFIANT
```

La sélection est enregistrée dans `task.method.architecture` avec le mode, la source, la stack et les
contraintes. Les agents reçoivent ce choix dans leur contexte. Les modes sont exclusifs ; fournir
`--stack` avec une boilerplate est refusé pour éviter de déclarer une stack différente de celle du
profil. Utiliser le mode sur mesure pour une adaptation qui remplace la stack.

L'utilisateur peut imposer librement une architecture sans boilerplate :

```bash
framework method architecture T-IDENTIFIANT --custom \
  --stack Django --stack PostgreSQL --constraint "Déploiement sur nos serveurs"
```

`--stack` et `--constraint` sont répétables. Avec `--existing`, l'agent examine les fichiers du projet,
repère les composants et interfaces effectivement présents, puis documente cette architecture.
Une sélection remplace intégralement la précédente : répéter les contraintes que l'on souhaite
conserver. Les tâches acceptées ou annulées ne peuvent être modifiées par cette commande.

## Épingler la base et relier les documents

La première sélection d'une boilerplate peut laisser sa révision indéterminée. Le cadrage reste
alors incomplet. L'agent doit consulter le dépôt réel et relever le commit qu'il examine, puis
répéter la commande avec `--revision` et son SHA complet de 40 caractères :

```bash
framework method architecture T-IDENTIFIANT --boilerplate nextjs-saas \
  --revision SHA_COMPLET_DU_COMMIT_EXAMINE \
  --constraint "Les données de chaque organisation restent isolées"
```

Le SHA de cet exemple est un emplacement à remplacer, pas une révision utilisable. Le framework
contrôle sa forme ; il ne contacte pas GitHub et n'atteste pas que l'agent a réellement inspecté ce
commit. Les sources consultées et les conclusions doivent être consignées dans le document.

L'agent écrit l'architecture : base/version, modules, responsabilités, interfaces, contraintes,
fonctionnalités reprises ou manquantes, décisions et contrôles nécessaires. Il l'enregistre ensuite
avec `method record --kind architecture`, en déclarant ses entrées `--input` (notamment le PRD en
Product). L'enregistrement inclut `architecture_basis`, l'empreinte du choix de socle et des contraintes.

Un choix explicite rend ce document obligatoire sur tous les parcours. Les stories Feature/Product
et le plan doivent le référencer directement ou via leurs entrées. Modifier la stack, une contrainte
ou la révision rend l'ancien document incompatible avec le choix courant et invalide la revue de
story correspondante. Réexaminer puis enregistrer les documents affectés et leur nouvelle revue.

Sans sélection explicite, les tâches existantes conservent leurs prérequis de méthode. La sélection
n'est pas un certificat de qualité et la revue examine le fond des décisions.

## Passer du profil au SaaS exécutable

Une tâche de fondation distincte doit porter le travail d'importation et de configuration dans le
projet applicatif. Elle fixe le périmètre, les critères et le budget de ce premier livrable :

1. Importer la révision choisie, conserver sa provenance et ses notices de licence.
2. Retirer les exemples inutiles et configurer le projet sans committer de secrets.
3. Réconcilier les instructions des agents avec les conventions du socle ; `framework init`
   refuse volontairement d'écraser des fichiers de consignes existants différents.
4. Vérifier les parcours réellement requis : accès utilisateur, organisations, permissions,
   facturation si utilisée, migrations et sauvegarde/restauration.
5. Stabiliser le design system et les contrats d'interface, puis faire relire le résultat.

Les coûts d'évaluation et d'adaptation du socle appartiennent à cette tâche de fondation. Les stories
suivantes réutilisent ses documents sans dupliquer sa facture. Les tarifs des services externes ne
sont pas estimés automatiquement. Les [règles de coût](costs.md) restent applicables.

## Construire notre propre boilerplate

C'est possible : le mode `--custom` permet de définir un socle original puis de le développer avec
les tâches et revues du framework. Le choix économique initial est de réutiliser une base MIT qui
convient, d'y ajouter nos conventions et les contrôles manquants, puis de conserver les adaptations
réutilisables dans un starter maintenu séparément.

Un équivalent fonctionnel complet de ShipSaaS demande sa propre feuille de route : authentification,
organisations et permissions, abonnements, administration, emails et jobs, design system, tests et
exploitation. Il ne sera pas produit par la seule commande de sélection. Pour limiter le contexte
et l'entretien, commencer par les modules nécessaires aux premiers produits, puis élargir à partir
d'usages validés. Aucun code de ShipSaaS n'est inclus ou nécessaire à cette démarche.
