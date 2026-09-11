# Agentic Codage

**Un framework portable pour coder avec plusieurs agents, garder une mémoire commune et mesurer le coût des livrables réellement acceptés.**

Codex, Claude Code, Cursor, GitHub Copilot dans VS Code ou Visual Studio, Gemini CLI et assistants génériques utilisent les mêmes contrats, commandes et preuves. Le modèle reste votre choix. La [carte HTML](docs/carte-du-code.html) constitue la vue de référence : les agents alimentent des fiches JSON, le framework les valide et assemble la carte.

Version **0.1.0** · Python **3.11+** · Git · aucune dépendance Python d’exécution · interface et documentation en français, instructions d’agents en anglais.

> Le framework coordonne le travail et conserve les preuves. Il ne lance pas de modèles, ne paie pas d’API, ne garantit pas une certification et ne remplace pas les protections du dépôt. Son périmètre exact est décrit dans [les limites](docs/limitations.md).

## Démarrer en cinq minutes

```bash
git clone https://github.com/SylvainChast/Agentic-codage.git
cd Agentic-codage
python3 bin/framework --help
python3 -m unittest discover -s tests -v
python3 bin/framework check
python3 bin/framework costs
python3 bin/framework map
```

Ouvrir `docs/carte-du-code.html` dans un navigateur. Il fonctionne hors ligne, sans serveur ni CDN. GitHub affiche le fichier source ; pour l’interface, ouvrir la copie locale. La carte est un **instantané**, pas un moniteur temps réel.

Pour installer la commande dans un environnement virtuel :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
framework --help
```

Sous Windows : `py -3 -m venv .venv`, puis `.venv\Scripts\Activate.ps1` et `python -m pip install .`. Le lancement direct fonctionne aussi avec `python bin/framework`. L’installation utilise setuptools pour construire le paquet ; l’exécution n’utilise que la bibliothèque standard.

## L’installer dans votre projet

Après installation de la commande :

```bash
cd /chemin/vers/votre-projet
git init                         # seulement si le projet n’est pas déjà un dépôt
framework init --name "Mon produit" --currency EUR
```

Configurer ensuite `.framework/policy.json` avec **les vrais tests de votre projet**. L’initialisation installe volontairement une vérification en échec tant que cette étape n’est pas faite. Elle refuse de remplacer un `AGENTS.md`, `CLAUDE.md` ou une règle existante : réconcilier explicitement les consignes avant d’installer.

Exemple de vérification Python :

```json
{"name":"tests","argv":["{python}","-m","unittest","discover","-s","tests","-v"],"timeout_seconds":180}
```

`{python}` en première position désigne l’interpréteur qui exécute le framework. Une commande est un tableau d’arguments, jamais une chaîne exécutée par un shell.

L’installation crée les fiches, les instructions et `docs/framework.md`. Elle ne modifie pas votre code, ne choisit pas votre stack et ne configure pas automatiquement les droits GitHub. Ajouter et committer les fichiers générés avant d’ouvrir des worktrees.

## Le parcours d’une mission

1. **Contractualiser** : objectif, critères, livrables, chemins modifiables, interfaces partagées, dépendances et budget.
2. **Réserver** : un worktree par mission, réservation atomique des chemins et interfaces.
3. **Exécuter** : un agent propriétaire ; enregistrer chaque tentative, coût et transmission.
4. **Vérifier** : exécuter les contrôles configurés ; conserver logs et empreinte du contenu.
5. **Revoir** : un autre acteur examine le changement et chaque critère.
6. **Accepter** : enregistrer l’acceptation sur les preuves courantes, libérer la réservation et régénérer la carte.

```bash
framework task create --title "Ajouter le calcul du total" --owner agent-a \
  --scope src/pricing.py --scope tests/test_pricing.py --resource api:pricing \
  --criterion "Le total inclut la taxe et refuse les montants négatifs" \
  --deliverable "Calcul du total testé" --budget-minor 2000 --max-runs 5
```

La commande renvoie un identifiant `T-…`. Les étapes suivantes utilisent cet identifiant :

```bash
framework lease acquire T-IDENTIFIANT --owner agent-a
framework task start T-IDENTIFIANT --actor agent-a
# L’agent implémente, puis enregistre son exécution.
framework run record T-IDENTIFIANT --actor agent-a --model "modele-observe" \
  --outcome succeeded --cost-source actual --llm-cost-minor 125 \
  --human-seconds 300 --human-rate-minor 6000 \
  --cost-note "Coût API relevé dans la facture" \
  --summary "Calcul et tests ajoutés" --next-step "Vérification puis revue indépendante"
framework verify T-IDENTIFIANT
framework task submit T-IDENTIFIANT --actor agent-a
```

L’exemple n’invente pas de preuve : `verify` exécute réellement les commandes. La suite, avec les identifiants de preuve et de revue, est dans [le guide complet](docs/workflow.md). Pour essayer tout le parcours dans un dépôt temporaire :

```bash
python3 examples/demo.py
```

La démonstration utilise des **coûts fictifs explicitement étiquetés**. Elle ne lance aucun LLM et ne facture rien.

## Mesurer ce qui coûte et ce qui est livré

`framework costs` et la vue **Coûts** distinguent :

- le coût connu de chaque tâche, avec tentatives ratées, revue, coordination et temps humain ;
- le coût total divisé par les tâches exécutées ;
- le coût total divisé par les tâches acceptées ;
- le coût total divisé par les livrables acceptés, **y compris les coûts des autres tâches échouées ou abandonnées**.

Les montants sont en **unités mineures entières** : 125 = 1,25 EUR. Une seule devise à deux décimales par projet. Aucun taux de change ni tarif de modèle n’est deviné. Un abonnement peut être ventilé avec une méthode explicite et la source `estimate`. Un coût absent reste `unknown` : le ratio concerné devient non calculable. Un zéro doit correspondre à une valeur renseignée, pas à une absence de facture.

[Formules, exemples, limites et budgets →](docs/costs.md)

## Fichiers pour les agents et éditeurs

| Outil | Fichiers livrés |
|---|---|
| Codex / assistants compatibles AGENTS | `AGENTS.md`, `.agents/skills/swarm-deliver/`, `.agents/skills/swarm-review/` |
| Claude Code | `CLAUDE.md`, `.claude/skills/swarm-deliver/`, `.claude/skills/swarm-review/` |
| Cursor | `.cursor/rules/agentic-codage.mdc`, `.cursor/skills/…` |
| Copilot, VS Code et Visual Studio | `.github/copilot-instructions.md` |
| Gemini CLI | `GEMINI.md` |
| Windsurf | `.windsurf/rules/agentic-codage.md` |
| Tout autre modèle | Lire `.framework/OPERATING.md`, puis utiliser la CLI ou transmettre les commandes à un opérateur |

La prise en compte automatique dépend de la version et des réglages de l’outil. Les fichiers sont générés depuis un socle commun ; `framework adapters --check` détecte leur divergence. Aucun fichier de paramètres ne vous impose de modèle, de serveur MCP ou de permission.

[Compatibilité, génération et ajout d’un outil →](docs/adapters.md)

## Organisation du dépôt

```text
README.md                      Entrée principale
src/agentic_codage/             CLI, stockage, réservations, contrôles, coûts, carte
src/agentic_codage/assets/      Instructions canoniques, skills, HTML et schémas JSON
.framework/                    Politique et mémoire versionnée de ce dépôt
.agents/ .claude/ .cursor/      Adaptateurs et skills générés
.github/                       Instructions Copilot, CI et protection proposée
.windsurf/                     Règle générée
bin/framework                  Lancement direct sans installation
examples/                      Petit produit et parcours exécutable
tests/                        Tests des invariants et parcours CLI
docs/                         Guides, décisions d’architecture et exigences qualité
```

Les réservations vivantes sont dans le répertoire Git commun (`git rev-parse --git-common-dir`), **hors de l’historique**. La mémoire durable reste dans `.framework/`. Les deux usages sont distincts.

## Documentation

| Lire pour… | Document |
|---|---|
| Suivre une mission de bout en bout | [Workflow](docs/workflow.md) |
| Trouver une commande et ses erreurs | [CLI](docs/cli.md) |
| Comprendre les coûts et budgets | [Coûts](docs/costs.md) |
| Comprendre les modules et les données | [Architecture](docs/architecture.md), [modèle de données](docs/data-model.md) |
| Utiliser un éditeur ou un modèle | [Adaptateurs](docs/adapters.md) |
| Préparer la due diligence technique | [Qualité et preuves](docs/quality.md) |
| Configurer CI, worktrees et intégration | [Exploitation](docs/operations.md) |
| Connaître les frontières du produit | [Limites](docs/limitations.md) |
| Contribuer ou signaler un problème | [Contribution](CONTRIBUTING.md), [sécurité](SECURITY.md) |
| Voir ce qui a été construit et vérifié | [Implémentation](docs/implementation.md), [changelog](CHANGELOG.md) |

## Vérifier le framework

```bash
python3 -m unittest discover -s tests -v
python3 bin/framework check
python3 bin/framework adapters --check
python3 bin/framework map
python3 bin/framework map --check
```

La CI répète les tests sur plusieurs systèmes et versions Python. Les contrôles locaux et les déclarations d’agents ne sont pas une frontière de sécurité : configurer des vérifications obligatoires et une revue réelle sur la branche protégée, comme décrit dans [l’exploitation](docs/operations.md).

## Licence

Aucune licence de redistribution n’est choisie dans cette première version. Avant une diffusion comme framework open source, le propriétaire doit choisir et ajouter la licence adaptée. Les licences et la provenance des dépendances des produits restent à inventorier séparément.
