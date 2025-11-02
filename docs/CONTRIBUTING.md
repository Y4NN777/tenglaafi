# Guide de Contribution - TengLaafi RAG

##  Équipe Hackathon

**TengLaafi** est développé par une équipe de 3 hackers passionnés :

- **Ali Guissou - Guali-spec** : Collecte de données & Intégrations
- **Ragnang-Newende Yanis Axel DAB0 - Y4NN777** : Architecture RAG, Pipeline IA, Tests & Evaluation
- **Fabrice Rachid Ramde** : API Backend & Interface Utilisateur

---

## Workflow de Développement

### Branches

```
main                            # Production (jamais push directement)
├── develop                      # Développement principal
│   ├── feature/rag-core         # Pipeline RAG
│   ├── feature/data-collection  # Collecte données
│   ├── feature/api-backend      # API FastAPI
│   ├── feature/frontend         # Interface utilisateur
│   ├── feature/evaluation       # Tests & métriques
│   └── feature/docs             # Documentation
```

### Règles de Branches

- **main** : Code en production, toujours stable
- **develop** : Intégration continue des features
- **feature/** : Développement des nouvelles fonctionnalités
- **hotfix/** : Corrections urgentes en production

---

##  Processus de Contribution

### 1. Préparation

```bash
# Clone le repo
git clone https://github.com/Y4NN777/tenglaafi.git
cd tenglaafi

# Crée ta branche feature
git checkout -b feature/ma-feature
```

### 2. Développement

```bash
# Active l'environnement
conda activate tenglaafi  # ou source venv/bin/activate

# Installe les dépendances
make install

# Setup du projet
make setup

# Travaille sur ta feature...
```

### 3. Tests Locaux

```bash
# Tests rapides
make test-fast

# Vérifications complètes
make check

# Tests d'intégration
make test-integration
```

### 4. Commit

#### Règles de Commit

```
type(scope): description courte

Corps du commit (optionnel)
- Détail des changements
- Impact sur le système
```

#### Types de Commit

- `feat:` Nouvelle fonctionnalité
- `fix:` Correction de bug
- `docs:` Documentation
- `style:` Formatage/code style
- `refactor:` Refactorisation
- `test:` Tests
- `chore:` Maintenance

#### Exemples

```bash
# Bonne pratique
git commit -m "feat(rag): add semantic search with ChromaDB

- Implement vector similarity search
- Add embedding caching for performance
- Update API endpoints for search queries"

# Évite
git commit -m "update code"
git commit -m "fix bug"
```

---

## Pull Request Process

### Template PR

```markdown
## Description
[Description claire de la fonctionnalité]

## Type de Changement
- [ ] Nouvelle fonctionnalité (feat)
- [ ] Correction de bug (fix)
- [ ] Refactorisation (refactor)
- [ ] Documentation (docs)
- [ ] Tests (test)

## Tests Réalisés
- [ ] Tests unitaires passent
- [ ] Tests d'intégration OK
- [ ] Tests de performance (si applicable)

## Checklist
- [ ] Code review effectué
- [ ] Documentation mise à jour
- [ ] Tests ajoutés/modifiés
- [ ] Fonctionnalité testée manuellement

## Impact
[Décrivez l'impact sur le système existant]
```

### Processus PR

1. **Push ta branche** vers GitHub
2. **Crée une Pull Request** vers `develop`
3. **Assigne un reviewer** (un autre membre de l'équipe)
4. **Code Review** : Au moins 1 approbation requise
5. **Merge** : Squash and merge vers `develop`

---

##  Standards de Qualité

### Code Quality

```bash
# Formatage automatique
make format

# Vérification style
make lint

# Tests complets
make test

```

### Tests Obligatoires

- **Coverage minimum** : 80%
- **Tests unitaires** : Tous les modules critiques
- **Tests d'intégration** : Pipeline RAG complet
- **Tests de performance** : Temps de réponse < 5s

---

##  Documentation

### Mise à Jour Docs

- **README.md** : Installation et usage
- **docs/** : Documentation technique détaillée
- **Code comments** : Docstrings pour toutes les fonctions

### Standards Docs

```python
def ma_fonction(param: str) -> dict:
    """
    Description courte de la fonction.

    Args:
        param: Description du paramètre

    Returns:
        Description de la valeur de retour

    Raises:
        ExceptionType: Quand cette exception est levée

    Example:
        >>> ma_fonction("test")
        {'result': 'ok'}
    """
```

---

## Gestion des Urgences

### Hotfix
```bash
# Crée une branche hotfix
git checkout -b hotfix/correction-urgente main

# Corrige le problème
# Tests...
# Commit...

# Merge vers main ET develop
git checkout main
git merge hotfix/correction-urgente

git checkout develop
git merge hotfix/correction-urgente
```

---

## Bonnes Pratiques

### Communication

- **Daily standup** : 15 min chaque matin
- **Slack** : Communication asynchrone
- **Trello** : Tracking des tâches

### Code Review

- **Constructive** : Focus sur l'amélioration
- **Respectueux** : Bienveillance entre teammates
- **Technique** : Discussion sur les choix techniques
---

##  Support & Aide

### Qui contacter ?

- **Questions techniques** : Ragnang-Newende (theY4NN) - y4nn.dev@gmail.com
- **Problèmes de déploiement** : Ragnang-Newende (theY4NN) - y4nn.dev@gmail.com
- **Questions fonctionnelles** : Ragnang-Newende (theY4NN) - y4nn.dev@gmail.com

### Ressources

- [Architecture](./ARCHITECTURE.md)
- [API Documentation](./API.md)
- [Tests Guide](./TESTING.md)

---

## Objectifs Hackathon

### Jours 1-2 : Setup & Core
- [ ] Pipeline RAG fonctionnel
- [ ] 500+ documents collectés
- [ ] API de base opérationnelle

### Jours 3 : Features & Polish
- [ ] Interface utilisateur
- [ ] Tests complets
- [ ] Optimisations performance

### Jour 4 : Présentation
- [ ] Démo fonctionnelle
- [ ] Slides de présentation
- [ ] Documentation finale

---

##  Règles d'Or

1. **Communique** : Toujours expliquer tes choix
2. **Teste** : Rien ne va en prod sans tests
3. **Documente** : Code + décisions importantes
4. **Review** : Tout le monde review le code des autres
5. **Fun** : On apprend et on s'amuse !

---

*Guide créé pour l'équipe TengLaafi - Hackathon 2024*