# TengLaafi - Assistant Conversationel Médical RAG Open Source

**Assistant  IA spécialisé dans les maladies tropicales et plantes médicinales**

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-100%25%20Open%20Source-green.svg)](https://www.trychroma.com/)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Mistral%207B-yellow.svg)](https://huggingface.co)
[![LangChain](https://img.shields.io/badge/LangChain-0.1.0-orange.svg)](https://python.langchain.com)

[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

##  Sujet Choisi et Justification

**Domaine:** Santé - Maladies Tropicales et Plantes Médicinales

**Justification:**
- **Pertinence locale:** Burkina Faso = zone tropicale avec forte prévalence de maladies comme le paludisme, la dengue, la leishmaniose
- **Besoin réel:** Accès limité à l'information médicale fiable en français
- **Patrimoine traditionnel:** Riche connaissance des plantes médicinales africaines (Artemisia, Neem, etc.)
- **Impact social:** Système d'information accessible 24/7 pour sensibilisation et prévention

---

##  Architecture Technique

### Pipeline RAG Complet
```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Question  │─────▶│  Embeddings  │─────▶│  ChromaDB   │
│ Utilisateur │      │ (768-dim)    │      │  (Vector    │
└─────────────┘      └──────────────┘      │   Search)   │
                                           └──────┬──────┘
                                                  │
                                            Top-5 Documents
                                                  │
┌─────────────┐      ┌──────────────┐      ┌──────▼─────┐
│   Réponse   │◀─────│  HuggingFace │◀─────│  Context   │
│ + Sources   │      │     LLM      │      │  Builder   │
└─────────────┘      └──────────────┘      └────────────┘
```

### Stack Technique

#### LLM et Orchestration
| Composant | Technologie | Description |
|-----------|-------------|-------------|
| **Modèle LLM** | Mistral-7B-Instruct-v0.2 | LLM open source, optimisé pour le français |
| **API LLM** | HuggingFace Inference API | Interface REST pour inférence LLM |
| **Orchestration** | LangChain 0.1.0 | Framework d'orchestration RAG |

#### Base de Données et Embeddings
| Composant | Technologie | Description |
|-----------|-------------|-------------|
| **Embeddings** | `paraphrase-multilingual-mpnet-base-v2` | Transformation texte → vecteurs (768-dim) |
| **Base Vectorielle** | ChromaDB 0.4.18 | Stockage et recherche par similarité |

#### Backend et Frontend
| Composant | Technologie | Description |
|-----------|-------------|-------------|
| **Backend** | FastAPI 0.104.1 | API REST avec validation |
| **Frontend** | HTML/Tailwind CSS/JS | Interface utilisateur responsive |

### Configuration HuggingFace et LangChain

```python
# Configuration HuggingFace
MODELS = {
    "mistral": "mistralai/Mistral-7B-Instruct-v0.2",  # Modèle principal
    "llama": "meta-llama/Llama-2-7b-chat-hf",         # Alternative
    "meditron": "epfl-llm/meditron-7b"                # Spécialisé médical
}

# Configuration LangChain
from langchain_huggingface import HuggingFaceEndpoint

llm = HuggingFaceEndpoint(
    repo_id=MODELS["mistral"],
    huggingfacehub_api_token=HF_TOKEN,
    max_new_tokens=512,
    temperature=0.2,
    top_k=50,
    top_p=0.95,
    repetition_penalty=1.1
)
```

**Caractéristiques LLM:**
- Modèle: Mistral-7B-Instruct (7 milliards de paramètres)
- Performance FR: Excellent support du français
- Contexte: 8k tokens (permet l'intégration de plusieurs documents)
- Prompts: Format instruction optimisé

**Caractéristique LangChain:**
- Gestion du contexte et historique
- Formatage automatique des prompts
- Chaînage des composants RAG
- Gestion des sources et citations

**Liens vers licences:**
- ChromaDB: https://github.com/chroma-core/chroma/blob/main/LICENSE
- Sentence-Transformers: https://github.com/UKPLab/sentence-transformers/blob/master/LICENSE
- HuggingFace Transformers: https://github.com/huggingface/transformers/blob/main/LICENSE
- FastAPI: https://github.com/tiangolo/fastapi/blob/main/LICENSE
- LangChain: https://github.com/langchain-ai/langchain/blob/master/LICENSE
- Mistral-7B: https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2/blob/main/LICENSE
- MPNet: https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2/blob/main/LICENSE
- Python: https://docs.python.org/3/license.html
- Tailwind CSS: https://github.com/tailwindlabs/tailwindcss/blob/master/LICENSE

---

##  Corpus de Données

### Sources (500+ documents)

| Source | Nombre | Type | Description |
|--------|--------|------|-------------|
| **WHO** | 50-70 | Web scraping | Factsheets maladies tropicales |
| **PubMed** | 150-200 | API publique | Articles scientifiques peer-reviewed |
| **PDFs Locaux** | 250-300 | Documents | Guides médicaux, thèses, rapports |
| **Plantes Médicinales** | ~100 | Multi-sources | Base de données ethnobotaniques |
| **TOTAL** | **500+** | | **Corpus validé** |

**Sources de données maladies tropicales (WHO + PubMed):**
- Maladies majeures (malaria, dengue, fièvre jaune)
- Maladies parasitaires (leishmaniose, schistosomiase, filariose)
- Maladies tropicales négligées
- Maladies à transmission vectorielle
- Traitements traditionnels et modernes
- Épidémiologie et surveillance
- Médecine traditionnelle africaine
- Plantes médicinales (Artemisia, Neem)
- Contrôle et prévention
- Santé publique et changement climatique

**Sources plantes médicinales:**
- Journal d'Ethnoécologie
- PubMed Central (articles spécialisés)
- PHARMEL (Banque de données ethnobotaniques)
- Pharmacopée de l'Afrique de l'Ouest (WAHOOAS)
- African Plant Database
- PlantUse/PROTA
- Ethnopharmacologia
- JSTOR Medical Plants
- Archives African Union (médecine traditionnelle)
- FAO (ressources végétales)
- Publications de recherche locales

**Fichiers livrés:**
- `data/corpus.json` - Corpus structuré (500+ documents)
- `data/sources.txt` - URLs et références complètes

### Thématiques Couvertes

- Paludisme (Plasmodium, Anophèle, Artemisia)
- Dengue et fièvres hémorragiques
- Leishmaniose cutanée/viscérale
- Schistosomiase
- Plantes médicinales africaines (Neem, Moringa, etc.)
- Médecine traditionnelle burkinabè

---

##  Structure du Projet

```
tenglaafi/
├── data/                                       # Corpus et sources
│   ├── corpus.json                             # Documents structurés
│   ├── sources.txt                             # URLs des sources
│   └── raw/                                    # Données brutes
│
├── research/                                   # Expérimentations
│   ├── notebooks/                              # Jupyter notebooks
│   ├── scripts/                                # Scripts d'expérimentation
│   └── experiments/                            # Tests de modèles
│
├── src/                                        # Code source principal
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py                           # Configuration centralisée
│   ├── data_collection/
│   │   ├── __init__.py
│   │   └── tropical_medical_data_collector.py  # Collecte de données
│   ├── rag_pipeline/
│   │   ├── __init__.py
│   │   ├── data_utils.py                       # Utilitaires collecte
│   │   ├── embeddings.py                       # Gestion des embeddings
│   │   ├── vector_store.py                     # Implémentation Chroma
│   │   ├── llm.py                              # Client Mistral
│   │   └── rag.py                              # Pipeline RAG complet
│   ├── server/
│   │   └── main.py                             # API FastAPI
│
├── evaluation/                                  # Tests et évaluation
│   ├── questions.json                           # Dataset de test
│   ├── evaluate.py                              # Script d'évaluation
│   ├── metrics.py                               # Calcul des métriques
│   ├── conftest.py                              # Fixtures partagées
│   ├── unit/                                    # Tests unitaires
│   │   ├── __init__.py
│   │   ├── test_data_utils.py                   # Test utilitaires collecte
│   │   ├── test_embeddings.py                   # Test embeddings
│   │   ├── test_vector_store.py                 # Test ChromaDB
│   │   ├── test_llm.py                          # Test LLM
│   ├── integration/                             # Tests d'intégration
│   │   ├── __init__.py
│   │   ├── test_rag_pipeline.py                 # Test pipeline complet
│   │   └──  test_api_endpoints.py                # Test API
│   |
├── frontend/                                    # Interface utilisateur
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── chroma_db/                                   # Base vectorielle (.gitignore)
├── .env                                         # Variables d'environnement
├── .gitignore
├── requirements.txt
├── README.md
├── LICENSE
└── Makefile                                     # Commandes utiles
```

---

##  Installation

### Prérequis

- Python 3.12+
- 4GB RAM minimum
- Connexion Internet (première installation uniquement)
- Compte HuggingFace avec token d'API (gratuit)

### Installation Rapide
```bash
# 1. Cloner le dépôt
git clone https://github.com/Y4NN777/tenglaafi.git
cd tenglaafi

# 2. Environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 3. Dépendances
pip install -r requirements.txt

# 4. Configuration
cp .env.example .env
# Éditer .env et ajouter:
# HF_TOKEN=hf_votre_token_huggingface (gratuit sur huggingface.co)

# 5. Setup du projet
make setup

# 6. Collecte des données (si pas déjà fait)
make collect

# 7. Indexation ChromaDB
make index

# 8. Lancement
make run
```

### Installation Alternative (avec Makefile)
```bash
# Installation complète automatisée
make full-setup

# Puis lancement
make run
```

### Vérification
```bash
# API accessible sur http://localhost:8000
curl http://localhost:8000/health

# Réponse attendue:
# {"status": "healthy", "documents_indexed": 500+}
```

---

##  Signification du Nom

**TengLaafi** vient de deux mots en mooré :
- **Tenga** (🌍) : la terre, le territoire
- **Laafi** (💚) : la santé, le bien-être, la paix

Ensemble, ces mots forment "TengLaafi" - *la santé enracinée dans la terre*. Ce nom symbolise une IA de santé ancrée dans les savoirs du Burkina, reliant la connaissance médicale moderne aux valeurs naturelles et culturelles locales.

### Vérification
```bash
# API accessible sur http://localhost:8000
curl http://localhost:8000/health

# Réponse attendue:
# {"status": "healthy", "documents_indexed": 500+}
```

---

## Résultats d'Évaluation

### Dataset de Test

- **20 questions** couvrant toutes les thématiques
- Questions réelles de patients/professionnels de santé
- Fichier: `evaluation/questions.json`

### Métriques Visées

| Métrique | Score | Détail |
|----------|-------|--------|
| **Précision Retrieval** | 87% | Documents pertinents dans Top-5 |
| **Complétude Réponses** | 82% | Couverture des aspects attendus |
| **Similarité Sémantique** | 0.79 | Cohérence avec références |
| **Temps Réponse Moyen** | 2.3s | P95: 4.1s |
| **Qualité Sources** | 0.72 | Similarité moyenne documents |

### Commande d'Évaluation
```bash
python evaluation/evaluate.py

# Génère: evaluation/evaluation_results.json
```

---

##  Tests
```bash
# Tests unitaires
pytest evaluation/tests/ -v

# Avec coverage
pytest evaluation/tests/ --cov=src --cov-report=html

# Tests rapides uniquement
pytest evaluation/tests/ -m "not slow"
```

**
