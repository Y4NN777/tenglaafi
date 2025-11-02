# Architecture Système - TengLaafi Chat

## Vue d'ensemble

TengLaafi est un système RAG (Retrieval-Augmented Generation) 100% open source spécialisé dans l'assistance médicale pour les maladies tropicales. L'architecture est modulaire, scalable et optimisée pour les environnements de recherche et production.

---

## Architecture Generale

```plaintext
┌──────────────────────────────────────────────────────────────────┐
│                    TENG LAAFI CHAT                               │
│                    ═══════════════                               │
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐           │
│  │   CLIENT    │    │    API      │    │   RAG       │           │
│  │   LAYER     │◄──►│   LAYER     │◄──►│   ENGINE    │           │
│  │             │    │             │    │             │           │
│  │ • Web UI    │    │ • FastAPI   │    │ • Pipeline  │           │
│  │ • REST API  │    │ • Pydantic  │    │ • Embeddings│           │
│  │ • Mobile    │    │ • CORS      │    │ • Vector DB │           │
│  └─────────────┘    └─────────────┘    └─────────────┘           │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                 DATA & INFRASTRUCTURE                       │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │ │
│  │  │  CORPUS     │ │  VECTOR     │ │   LLM       │            │ │
│  │  │  STORAGE    │ │  STORE      │ │   ENGINE    │            │ │
│  │  │             │ │             │ │             │            │ │
│  │  │ • JSON      │ │ • ChromaDB  │ │ • Mistral   │            │ │
│  │  │ • Sources   │ │ • Embeddings│ │ • HF API    │            │ │
│  │  │ • Metadata  │ │ • Search    │ │ • Cache     │            │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘            │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                 DEVELOPMENT & MONITORING                    │ │
│  │  ┌──────────────┐ ┌─────────────┐ ┌─────────────┐           │ │
│  │  │   TESTS      │ │ EVALUATION  │ │  LOGGING    │           │ │
│  │  │              │ │             │ │             │           │ │
│  │  │ • Unit       │ │ • Metrics   │ │ • Files     │           │ │
│  │  │ • Integration│ │ • Benchmarks│ │ • Console   │           │ │
│  │  │ • Performance│ │ • Reports   │ │ • Monitoring│           │ │
│  │  └──────────────┘ └─────────────┘ └─────────────┘           │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

##  Flux de Données - Pipeline RAG

### 1. Phase de Collecte (Data Ingestion)

```
Internet Sources ──► Web Scraper ──► Text Processing ──► Corpus JSON
     │                       │                │
     ├─ WHO Fact Sheets      ├─ BeautifulSoup ├─ Cleaning
     ├─ PubMed Articles      ├─ PDF Extraction├─ Normalization
     ├─ Medical PDFs         ├─ Validation    ├─ Chunking
     └─ Research Papers      └─ Rate Limiting └─ Metadata
```

**Composants**:
- `WebScraper`: Extraction HTML/PDF avec BeautifulSoup
- `PubMedAPI`: Client API PubMed E-utilities
- `PDFLoader`: Traitement PDFs avec LangChain
- `Text Processing`: Nettoyage et validation du contenu

### 2. Phase d'Indexation (Vector Store)

```
Corpus JSON ──► Embedding Model ──► Vector Store ──► Search Index
      │                │                    │
      ├─ Documents     ├─ Sentence-BERT     ├─ ChromaDB
      ├─ Metadata      ├─ 768 dimensions    ├─ Collections
      ├─ Sources       ├─ Normalization     ├─ Persistence
      └─ Validation    └─ Batch Processing  └─ Optimization
```

**Composants**:
- `EmbeddingManager`: Gestion SentenceTransformers
- `ChromaVectorStore`: Base vectorielle persistante
- `Batch Processing`: Traitement par lots pour performance

### 3. Phase de Query (RAG Pipeline)

```
User Question ──► Query Processing ──► Retrieval ──► Generation ──► Response
       │                   │                │              │
       ├─ Natural Language ├─ Embedding     ├─ Similarity  ├─ Context
       ├─ Validation       ├─ Search        ├─ Ranking     ├─ Prompt
       └─ Sanitization     └─ Filtering     └─ Top-K       └─ LLM
```

**Étapes détaillées**:

#### 3.1 Query Processing
```
Question ──► Validation ──► Sanitization ──► Embedding ──► Query Vector
```

#### 3.2 Retrieval
```
Query Vector ──► Vector Search ──► Similarity Scores ──► Top-K Documents
                      │                        │
                      ├─ Cosine Similarity     ├─ Ranking
                      ├─ ChromaDB Query        ├─ Threshold
                      └─ Metadata Filtering   └─ Diversity
```

#### 3.3 Context Building
```
Top-K Docs ──► Text Extraction ──► Context Assembly ──► Prompt Template
      │                │                    │
      ├─ Full Text      ├─ Chunk Selection   ├─ System Prompt
      ├─ Metadata       ├─ Length Limits     ├─ User Question
      └─ Sources        └─ Overlap Handling  └─ Instructions
```

#### 3.4 Generation
```
Prompt ──► LLM API ──► Response ──► Post-Processing ──► Final Answer
     │           │            │              │
     ├─ HF API   ├─ Mistral   ├─ Cleaning    ├─ Citations
     ├─ Timeout  ├─ Streaming ├─ Validation  ├─ Sources
     └─ Retry    └─ Cache     └─ Formatting  └─ Metadata
```

---

##  Architecture Modulaire

### Core Layer (`src/core/`)

```
config.py
├── Configuration centralisée
├── Variables d'environnement
├── Logging setup
├── Chemins et constantes
└── Validation des paramètres
```

### Data Collection Layer (`src/data_collection/`)

```
tropical_medical_data_collector.py
├── Orchestrateur de collecte
├── Gestion des sources multiples
├── Pipeline de traitement
├── Sauvegarde corpus
└── Statistiques et métriques
```

```
data_utils.py
├── WebScraper (HTML/PDF)
├── PubMedAPI client
├── PDFLoader
├── Text cleaning utilities
└── Content validation
```

### RAG Pipeline Layer (`src/rag_pipeline/`)

```
embeddings.py
├── EmbeddingManager singleton
├── SentenceTransformers wrapper
├── Batch processing
├── Cache management
└── Similarity computation
```

```
vector_store.py
├── ChromaVectorStore wrapper
├── Collection management
├── Document indexing
├── Search operations
├── Health checks
└── Persistence handling
```

```
llm.py
├── MedicalLLM client
├── HuggingFace API wrapper
├── Prompt engineering
├── Response processing
├── Error handling
└── Rate limiting
```

```
rag.py
├── RAGPipeline orchestrator
├── Query processing
├── Context building
├── Response enhancement
├── Cache implementation
└── Batch operations
```

### Server Layer (`src/server/`)

```
main.py
├── FastAPI application
├── Route definitions
├── Middleware setup
├── Error handling
├── CORS configuration
└── Static file serving
```

---

## Stockage et Persistance

### Corpus Storage

```
data/
├── corpus.json          # Documents structurés
├── sources.txt          # Métadonnées sources
└── raw/                 # PDFs et fichiers bruts
```

**Format JSON**:
```json
[
  {
    "id": 123,
    "title": "Malaria Treatment Guidelines",
    "text": "Full document text...",
    "url": "https://who.int/malaria",
    "source": "WHO",
    "length": 2500,
    "timestamp": "2024-01-15T10:30:00Z"
  }
]
```

### Vector Store (ChromaDB)

```
chroma_db/
├── Collections persistantes
├── Embeddings indexés
├── Metadata index
└── Configuration
```

**Structure ChromaDB**:
- **Collection**: `tropical_medicine`
- **Documents**: Textes complets
- **Embeddings**: Vecteurs 768D normalisés
- **Metadatas**: Titre, URL, longueur, source

### Simple Cache System

```
In-memory cache (RAGPipeline)
├── Query → Response mapping
├── LRU eviction (100 entries)
├── Similarity-based keys
└── Performance optimization
```

---

##  Technologies et Dépendances

### Core Dependencies

```python
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0

# Data Processing
requests==2.31.0
beautifulsoup4==4.12.2
python-dotenv==1.0.0

# AI/ML
sentence-transformers==2.2.2
chromadb==0.4.18
numpy==1.24.3

# LLM
langchain-huggingface==0.0.3

# Development
pytest==7.4.3
black==23.11.0
flake8==6.1.0
```

### Architecture Decisions

#### Pourquoi ChromaDB ?
- **Open Source**: 100% gratuit et transparent
- **Local**: Pas de dépendance cloud
- **Performant**: Recherche vectorielle optimisée
- **Persistant**: Stockage disque automatique
- **Simple**: API Python intuitive

#### Pourquoi SentenceTransformers ?
- **Spécialisé médical**: Modèles multilingues
- **Optimisé**: Calculs vectoriels rapides
- **Normalisé**: Cosine similarity prête
- **Batch processing**: Traitement efficace

#### Pourquoi Mistral via HF ?
- **Open Source**: Modèle transparent
- **Performant**: Qualité GPT-4 comparable
- **API simple**: HuggingFace Inference
- **Coût**: Gratuit (quotas généreux)

---

## ⚡ Optimisations et Performance

### 1. Embedding Optimizations

```
Batch Processing
├── Taille lots: 32 documents
├── GPU acceleration (si disponible)
├── Cache embeddings fréquents
└── Normalisation automatique

Memory Management
├── Lazy loading des modèles
├── Singleton patterns
├── Garbage collection
└── Memory profiling
```

### 2. Vector Search Optimizations

```
Index Structure
├── HNSW algorithm (ChromaDB)
├── 768 dimensions
├── Cosine similarity
└── Metadata filtering

Query Optimization
├── Top-K retrieval (5 docs)
├── Score thresholding
├── Diversity ranking
└── Cache des requêtes fréquentes
```

### 3. LLM Optimizations

```
API Management
├── Connection pooling
├── Retry logic (2 tentatives)
├── Timeout handling (30s)
├── Rate limiting awareness

Prompt Engineering
├── Context window: 3000 chars
├── System prompt médical
├── Source citations
└── Response formatting
```

### 4. System Optimizations

```
Caching Strategy
├── In-memory LRU cache
├── Query deduplication
├── Embedding reuse
└── Response caching

Async Processing
├── Non-blocking I/O
├── Concurrent requests
├── Background tasks
└── Streaming responses
```

---

##  Tests et Qualité

### Test Architecture

```
tests/
├── unit/                    # Tests unitaires isolés
│   ├── test_embeddings.py
│   ├── test_vector_store.py
│   ├── test_llm.py
│   └── test_data_utils.py
├── integration/             # Tests d'intégration
│   ├── test_rag_pipeline.py
│   ├── test_api_endpoints.py
│   └── test_data_collection.py
└── performance/             # Tests de performance
    └── test_load.py
```

### Métriques d'Évaluation

```
Retrieval Metrics
├── Precision@K (retrieval precision)
├── Recall@K (retrieval recall)
├── Mean Reciprocal Rank (MRR)
└── Normalized Discounted Cumulative Gain (NDCG)

Generation Metrics
├── Answer completeness
├── Semantic similarity (BERTScore)
├── Factual accuracy
└── Source attribution

Performance Metrics
├── Query latency (target: <5s)
├── Throughput (queries/second)
├── Memory usage
└── CPU utilization
```

---

##  Sécurité et Robustesse

### Input Validation

```
Query Validation
├── Length checks (3-500 chars)
├── Content filtering
├── Sanitization
└── Rate limiting (future)

Data Validation
├── Source authenticity
├── Content quality checks
├── Metadata validation
└── Duplicate detection
```

### Error Handling

```
Graceful Degradation
├── Fallback responses
├── Partial results
├── Error logging
└── User-friendly messages

Monitoring
├── Health checks
├── Performance metrics
├── Error tracking
└── Alert system
```

---

##  Déploiement et Scaling

### Development Environment

```
Local Setup
├── Python 3.12 venv
├── ChromaDB local
├── HF API (cloud)
└── SQLite backend
```

### Production Environment

```
Docker Container
├── Python slim image
├── ChromaDB persistent volume
├── Environment variables
└── Health checks

Scaling Options
├── Horizontal scaling (multiple instances)
├── Load balancer (nginx)
├── Redis cache (future)
└── Database clustering (future)

```

---

## Évolutivité et Extensions

### Planned Enhancements

```
Multi-modal RAG
├── Image processing
├── Medical imaging
├── Document OCR
└── Multi-format support

Advanced Retrieval
├── Hybrid search (keyword + vector)
├── Re-ranking (cross-encoders)
├── Query expansion
└── Conversational memory

Multi-language Support
├── Language detection
├── Cross-lingual embeddings
├── Translated responses
└── Cultural adaptation
```

### API Extensions

```
Additional Endpoints
├── /conversations (chat history)
├── /feedback (user ratings)
├── /analytics (usage stats)
├── /admin (system management)
└── /webhooks (integrations)
```

---

## Monitoring et Observabilité

### Metrics Collection

```
Application Metrics
├── Request count/rate
├── Response times
├── Error rates
├── Cache hit rates

Business Metrics
├── Questions answered
├── User satisfaction
├── Popular topics
└── Source utilization

System Metrics
├── CPU/Memory usage
├── Disk I/O
├── Network traffic
└── Database performance
```

### Logging Strategy

```
Structured Logging
├── JSON format
├── Log levels (DEBUG/INFO/WARN/ERROR)
├── Request tracing
├── Error context
└── Performance timing
```

---

##  Points Forts de l'Architecture

###  Avantages

1. **100% Open Source**: Transparence et reproductibilité
2. **Modulaire**: Facilement extensible et maintenable
3. **Performant**: Optimisations pour la latence et le débit
4. **Robuste**: Gestion d'erreurs et récupération automatique
5. **Testable**: Architecture favorisant les tests automatisés
6. **Documentée**: Code et API bien documentés
7. **Scalable**: Architecture prête pour la montée en charge

###  Hackathon Optimization

1. **Rapid Development**: Structure claire pour 3 développeurs
2. **Quick Iteration**: Tests automatisés et déploiement facile
3. **Demonstration Ready**: API REST et interface web
4. **Evaluation Framework**: Métriques intégrées
5. **Production Ready**: Code de qualité professionnelle

---

##  Ressources et Références

### Architecture Patterns
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [RAG Systems Design](https://arxiv.org/abs/2005.11401)

### Technologies
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [SentenceTransformers Guide](https://www.sbert.net/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)

### Performance
- [Vector Databases Comparison](https://superlinked.com/vector-db-comparison)
- [LLM API Optimization](https://huggingface.co/docs/api-inference/index)
- [RAG Performance Tuning](https://arxiv.org/abs/2312.10997)

---

*Architecture Documentation - TengLaafi RAG System v1.0.0*