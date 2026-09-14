# Modèles, éditeurs et skills

## Une source commune

La source maintenue dans ce framework est `src/agentic_codage/assets/operating.md`. L’installation
la copie vers `.framework/OPERATING.md`. Les petits fichiers d’entrée indiquent de lire ce contrat,
la politique du projet et le contexte ciblé. Les skills ajoutent uniquement la procédure utile au rôle.

| Surface | Entrée | Fonction |
|---|---|---|
| Codex et AGENTS | `AGENTS.md` | Instructions de dépôt |
| Codex / Agent Skills | `.agents/skills/swarm-deliver/SKILL.md`, `swarm-review/SKILL.md` | Réalisation et revue |
| Claude Code | `CLAUDE.md`, `.claude/skills/…` | Instructions et skills |
| Cursor | `.cursor/rules/agentic-codage.mdc`, `.cursor/skills/…` | Règle alwaysApply et skills |
| GitHub Copilot | `.github/copilot-instructions.md` | Instructions pour VS Code, Visual Studio et surfaces compatibles |
| Gemini CLI | `GEMINI.md` | Point d’entrée projet |
| Windsurf | `.windsurf/rules/agentic-codage.md` | Règle de projet |
| Assistant générique | `.framework/OPERATING.md` + JSON + CLI | Mode manuel ou appel d’outils |

Les modèles ne sont pas des éditeurs. Un modèle ayant accès aux fichiers et à une commande peut
participer directement ; un modèle de conversation sans outils peut préparer une contribution que
l’opérateur exécute. Ne jamais lui attribuer une vérification qu’il n’a pas exécutée.

## Skills livrés

- **swarm-deliver** : entrer dans un contrat, réserver, exécuter, comptabiliser, vérifier et transmettre.
- **swarm-orchestrate** : choisir les profils, lancer et suivre le contrôleur borné.
- **swarm-review** : comparer le diff et les preuves aux critères sans réimplémenter le travail.

Le rôle d’arbitre est décrit dans le workflow : il s’active lors d’un désaccord sémantique, sans imposer
un agent permanent. La configuration `.framework/orchestration.json` associe chaque rôle à un modèle
choisi par l’utilisateur et un transport. Voir [l’orchestration](orchestration.md) pour les CLI natives
et le pont JSON générique ; les règles d’éditeur seules ne lancent aucun modèle.

## Générer et mettre à jour

```bash
framework adapters
framework adapters --check
```

La première commande crée seulement les fichiers manquants. Une divergence existante provoque un
refus explicite ; elle n’écrase jamais un travail antérieur. Dans le dépôt du framework, modifier
les assets canoniques, examiner le diff, puis réécrire explicitement les copies générées depuis
`adapter_files()` (API Python de `bootstrap.py`). Dans un produit, conserver les spécificités dans
la politique et les décisions ; une adaptation du contrat commun doit être maintenue comme telle.
La v0.1 ne propose pas de fusion automatique de règles ni de migration silencieuse entre versions.

Après changement de framework, examiner toutes les différences avant de remplacer les copies.
La CI `adapters --check` détecte la dérive des fichiers ; elle ne prouve pas qu’un modèle a lu ou
respecté les instructions. Vérifier les réglages de chargement dans chaque éditeur.

## Sources des formats

Formats principaux consultés le 11 septembre 2026 :

- [Codex — AGENTS.md](https://developers.openai.com/codex/guides/agents-md)
- [Codex — skills](https://developers.openai.com/codex/skills)
- [Claude Code — mémoire](https://code.claude.com/docs/en/memory)
- [Claude Code — skills](https://code.claude.com/docs/en/skills)
- [Cursor — règles](https://prod.cursor.com/docs/rules)
- [VS Code — instructions](https://code.visualstudio.com/docs/agent-customization/custom-instructions)
- [Visual Studio — contexte Copilot](https://learn.microsoft.com/en-us/visualstudio/ide/copilot-chat-context)

Les fichiers sont générés et vérifiés localement ; une session réelle dans chaque éditeur n’est pas
couverte par les tests automatisés du framework. Les adaptateurs complémentaires Gemini et Windsurf
restent des entrées simples ; leur comportement dépend de la version installée.

## Skills et commandes de méthode

Les onze procédures de cadrage et développement sont maintenues dans `assets/method/`, installées
sous `.framework/method/`. Les entrées de chaque outil renvoient à cette source et au contexte
ciblé fourni par la CLI. Les gabarits PRD/story sont générés depuis leurs schémas, sans copie des
rubriques à maintenir dans chaque adaptateur.

| Hôte | Entrées de méthode générées |
| --- | --- |
| Codex / Agent Skills | `.agents/skills/swarm-ETAPE/SKILL.md` ; le skill `swarm-review` existant est conservé et complété |
| Claude Code | `.claude/skills/ETAPE/SKILL.md` |
| Cursor | `.cursor/skills/ETAPE/SKILL.md` |
| VS Code / Copilot | `.github/prompts/ETAPE.prompt.md` |
| Gemini CLI | `.gemini/commands/ETAPE.toml` |
| Cascade / Windsurf | `.windsurf/workflows/ETAPE.md` |

La prise en charge des commandes natives varie selon l’hôte et les noms réservés. Le format de
prompt VS Code n’est pas une garantie de commande slash dans Visual Studio ; utiliser ses
instructions projet et la CLI lorsque nécessaire. Les formats ont été vérifiés avec leurs
sources officielles, sans simuler une session utilisateur dans chaque IDE. Voir le
[guide, les commandes et leurs sources](methodologie.md#commandes-dans-les-agents).
