# Petit produit de démonstration

Calcul monétaire en centimes, taxe en points de base et trois tests métier.

```bash
python3 -m unittest discover -s tests -v
```

Le parcours `../demo.py` copie ce produit dans un répertoire temporaire, initialise le framework,
crée une mission, enregistre des coûts **fictifs**, exécute réellement ces tests et exerce le mécanisme
de revue/acceptation avec des identités de simulation. Aucun agent LLM ni vraie revue indépendante
n’est invoqué par cette démonstration. Ne pas utiliser ses coûts comme données de production.
