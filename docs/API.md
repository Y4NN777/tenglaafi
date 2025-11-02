# API Documentation - TengLaafi RAG

## Vue d'ensemble

L'API TengLaafi fournit une interface REST complete pour interagir avec le systeme RAG medical. Elle est construite avec FastAPI et offre des endpoints pour poser des questions, gerer l'indexation, et surveiller les performances.

**Base URL**: `http://localhost:8000`
**Version**: 1.0.0
**Framework**: FastAPI + Uvicorn

---

## Endpoints Principaux

### 1. Page d'accueil
**GET** `/`

Page d'accueil HTML avec liens vers la documentation et l'interface utilisateur.

**Response**: HTML
```html
<html>
  <head><title>Vitali API</title></head>
  <body>
    <h1>Vitali - API RAG Médicale</h1>
    <p>Assistant médical intelligent avec Retrieval-Augmented Generation</p>
    <a href="/docs">Documentation API</a>
    <a href="/static/index.html">Interface Chat</a>
  </body>
</html>
```

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

### 4. Batch Query - Questions en Lot
**POST** `/batch_query`

Traite plusieurs questions en une seule requête (max 10 questions).

**Request Body**:
```json
{
  "questions": [
    "Quels sont les symptômes du paludisme?",
    "Comment traiter la dengue?",
    "Quelles plantes médicinales contre le paludisme?"
  ]
}
```

**Response Model**:
```json
{
  "results": [
    {
      "question": "Quels sont les symptômes du paludisme?",
      "answer": "Les symptômes incluent fièvre, frissons...",
      "sources": [...]
    }
  ],
  "count": 3
}
```

---

### 5. Suggestions - Questions Similaires
**GET** `/suggestions`

Retourne des suggestions de questions similaires pour améliorer la recherche.

**Paramètres Query**:
- `question` (string, required): Question de référence

**Response Model**:
```json
{
  "suggestions": [
    "En savoir plus sur: Traitement du paludisme",
    "En savoir plus sur: Symptômes de la malaria",
    "En savoir plus sur: Prévention paludisme Afrique"
  ]
}
```

**Exemple**:
```bash
curl "http://localhost:8000/suggestions?question=paludisme"
```

---

### 6. Statistiques Système
**GET** `/stats`

Retourne des statistiques détaillées sur le système et le corpus.

**Response Model**:
```json
{
  "total_documents": 512,
  "total_characters": 1250000,
  "avg_doc_length": 2441.41,
  "embedding_dimension": 768
}
```

---

### 7. Réindexation - Administration
**POST** `/reindex`

Force la réindexation complète du corpus (opération longue, utiliser avec précaution).

**Response Model**:
```json
{
  "status": "reindexed",
  "documents": 512,
  "message": "Corpus réindexé avec succès"
}
```

**Attention**: Cette operation peut prendre plusieurs minutes.

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

# Statistiques système
make stats

# Test de requête
make query-test
```

### Profiling

```bash
# Profiling des performances
make profile

# Analyse des résultats
python -c "import pstats; p = pstats.Stats('profile.stats'); p.print_stats()"
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

### Tests de Performance

```bash
# Benchmark API
make benchmark

# Tests de charge
pytest evaluation/tests/performance/ -v
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

## Deploiement

### Docker

```bash
# Build image
make docker-build

# Lancement container
make docker-run

# Logs
make docker-logs
```

### Production

```bash
# Avec Gunicorn (recommande)
gunicorn src.server.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

# Avec reverse proxy (nginx)
# Configuration nginx pour /api/* vers FastAPI
```

---

## Exemples d'utilisation

### Client Python

```python
import requests

class TengLaafiClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def query(self, question, include_sources=True, top_k=5):
        response = requests.post(
            f"{self.base_url}/query",
            json={
                "question": question,
                "include_sources": include_sources,
                "top_k": top_k
            }
        )
        return response.json()

    def health_check(self):
        response = requests.get(f"{self.base_url}/health")
        return response.json()

# Utilisation
client = TengLaafiClient()
result = client.query("Comment traiter le paludisme?")
print(result["answer"])
```

### Client JavaScript

```javascript
class TengLaafiAPI {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
    }

    async query(question, options = {}) {
        const response = await fetch(`${this.baseURL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question,
                include_sources: options.includeSources ?? true,
                top_k: options.topK ?? 5
            })
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    }

    async getSuggestions(question) {
        const response = await fetch(
            `${this.baseURL}/suggestions?question=${encodeURIComponent(question)}`
        );
        return await response.json();
    }
}

// Utilisation
const api = new TengLaafiAPI();
const result = await api.query("Quels sont les symptômes de la dengue?");
console.log(result.answer);
```

---

##  Dépannage

### Erreurs Courantes

#### "Service unhealthy"
```json
{"detail": "Service unhealthy: ChromaDB connection failed"}
```
**Solution**: Vérifier que l'index est initialisé (`make check-index`)

#### "Question trop courte"
```json
{"detail": "Question trop courte (minimum 3 caractères)"}
```
**Solution**: Poser une question plus détaillée

#### "Rate limit exceeded"
```json
{"detail": "Rate limit exceeded"}
```
**Solution**: Attendre quelques minutes, vérifier le quota HuggingFace

### Debugging

```bash
# Logs détaillés
tail -f logs/app.log

# Test manuel
curl -v http://localhost:8000/health

# Profiling requête
time curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Test question"}'
```

---

## Metriques et Performance

### Latences Typiques

- Health check: < 100ms
- Query simple: 2-5 secondes
- Batch query (10 questions): 15-30 secondes
- Réindexation: 5-15 minutes

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