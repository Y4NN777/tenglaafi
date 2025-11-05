# API Documentation - TengLaafi

## Vue d'ensemble

L'API TengLaafi fournit une interface REST complete pour interagir avec le systeme RAG medical. Elle est construite avec FastAPI et offre des endpoints pour poser des questions, gerer l'indexation, et surveiller les performances.

**Base URL**: `http://localhost:8000`
**Version**: 1.0.0
**Framework**: FastAPI + Uvicorn

---

## Endpoints Principaux

### 1. Interface utilisateur

**GET** `/`

L'interface utilisateur pour chat.

---

### 2. Health Check
**GET** `/health`

Vérifie la santé du système et retourne des statistiques de base.

**Response Model**:
```json
{
  "status": "healthy",
  "documents_indexed": 512,
  "model": "Mistral + Chroma"
}
```

**Exemple**:
```bash
curl http://localhost:8000/health
```

---

### 3. Query RAG - Questions Médicales
**POST** `/query`

Endpoint principal pour poser des questions médicales au système RAG.

**Request Body**:
```json
{
  "question": "Quels sont les symptômes du paludisme?",
  "include_sources": true,
  "top_k": 5
}
```

**Paramètres**:
- `question` (string, required): Question médicale en langage naturel (min 3 caractères)
- `include_sources` (boolean, optional): Inclure les documents sources (défaut: true)
- `top_k` (integer, optional): Nombre de documents à récupérer (1-10, défaut: 5)

**Response Model**:
```json
{
  "answer": "Le paludisme présente plusieurs symptômes...",
  "sources": [
    {
      "id": 123,
      "title": "Malaria - WHO Fact Sheet",
      "url": "https://who.int/malaria",
      "similarity": 0.87
    }
  ],
  "processing_time": 2.34
}
```

**Exemples d'utilisation**:

```bash
# Question simple
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Comment prévenir la dengue?"}'

# Avec sources détaillées
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quels sont les effets secondaires de l'"artemisia"?",
    "include_sources": true,
    "top_k": 3
  }'
```

**Codes d'erreur**:
- `422`: Validation error (question trop courte, top_k invalide)
- `500`: Erreur serveur (problème RAG)

---

## Configuration et Environnement

### Variables d'environnement

```env
# HuggingFace (obligatoire)
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Configuration LLM
LLM_MODEL=mistral  # mistral | meditron | llama

# ChromaDB
CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION_NAME=tropical_medicine

# API
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
```

### Démarrage du serveur

```bash
# Mode développement (auto-reload)
make dev

# Mode production
make run

# Avec logs debug
LOG_LEVEL=DEBUG make run
```

---

##  Monitoring et Debugging

### Logs d'API

Tous les endpoints loguent automatiquement :
- Timestamp
- Méthode HTTP
- URL
- Code de statut
- Temps de traitement

### Health Checks

```bash
# Vérification santé
make health

# Test de requête
make query-test
```

---

## Tests API

### Tests Unitaires

```bash
# Tests API uniquement
pytest evaluation/tests/integration/test_api_endpoints.py -v

# Tests d'intégration complets
make test-integration
```

---

## Securite et Limitations

### Rate Limiting

- Pas de rate limiting implémenté actuellement
- Recommandé pour production : ajout de middleware

### Validation

- Questions : minimum 3 caractères
- top_k : entre 1 et 10
- Batch : maximum 10 questions

### Gestion d'erreurs

L'API retourne des erreurs structurées :
```json
{
  "detail": "Question trop courte (minimum 3 caractères)"
}
```

---

### Optimisations

- Cache des embeddings activé
- Recherche vectorielle optimisée
- Pool de connexions HTTP
- Compression des réponses

---

## Liens Utiles

- [Documentation FastAPI](https://fastapi.tiangolo.com/)
- [Guide d'utilisation](../README.md)
- [Architecture système](./ARCHITECTURE.md)
- [Tests et évaluation](../evaluation/)

---

*Documentation API TengLaafi RAG - Version 1.0.0*