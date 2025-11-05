# TengLaafi - Assistant Conversationel RAG Open Source

**Assistant  IA spécialisé dans les maladies tropicales et plantes médicinales**

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-100%25%20Open%20Source-green.svg)](https://www.trychroma.com/)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Mistral%207B-yellow.svg)](https://huggingface.co)
[![LangChain](https://img.shields.io/badge/LangChain-orange.svg)](https://python.langchain.com)

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
| **Orchestration** | LangChain | Framework d'orchestration RAG |

#### Base de Données et Embeddings
| Composant | Technologie | Description |
|-----------|-------------|-------------|
| **Embeddings** | `paraphrase-multilingual-mpnet-base-v2` | Transformation texte → vecteurs (768-dim) |
| **Base Vectorielle** | ChromaDB 0.4.18 | Stockage et recherche par similarité |

#### Backend et Frontend
| Composant | Technologie | Description |
|-----------|-------------|-------------|
| **Backend** | FastAPI   | API REST avec validation |
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
| **WHO** | 23 | Web scraping | Factsheets maladies tropicales |
| **PubMed** | 254 | API publique | Articles scientifiques peer-reviewed |
| **PDFs Locaux** | 1243 | Documents | Guides médicaux, thèses, rapports |
| **Plantes Médicinales** | 11| Multi-sources | Base de données ethnobotaniques |
| **TOTAL** | **500+**(1531) | | **Corpus validé** |



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
│
├── app.log                              # logs d’exécution (temporaire / ignoré par git)
│
├── chroma_db/                           # base locale pour la base vectorielle Chroma (embeddings)
│
├── data/                                # jeux de données utilisés par le projet
│   ├── corpus.json                      # corpus consolidé pour le RAG
│   ├── sources.txt                      # liste des sources textuelles importées
│   │
│   └── raw/                             # données sources brutes non nettoyées
│       ├── 2013_pharmacopee_des_plantes_medicinales_afrique_ouest.pdf
│       ├── african_traditional_medicine_e.pdf
│       └── oms_burkina_faso_bulletin_information_t2_2025.pdf
│
├── docs/                                # documentation technique et fonctionnelle du projet
│   ├── API.md                           # spécification de l’API
│   ├── ARCHITECTURE.md                  # schéma et organisation technique
│   ├── CONTRIBUTING.md                  # règles de contribution au code
│   └── EVALUATION.md                    # description de la méthodologie d’évaluation
│
├── evaluation/                          # ensemble des scripts et résultats d’évaluation du modèle
│   ├── evaluation_results/              # fichiers de résultats (CSV, JSON)
│   │   ├── evaluation_results.csv
│   │   └── evaluation_results.json
│   │
│   ├── questions.json                   # 20 questions pour l’évaluation
│   │
│   ├── scripts/                         # scripts d’évaluation et de métriques
│   │   ├── evaluate.py
│   │   └── metrics.py
│   │
│   └── tests/                           # tests unitaires et d’intégration liés à l’évaluation
│       ├── conftest.py                  # configuration pytest commune
│       │
│       ├── integration/                 # tests d’intégration finaux du pipeline
│       │   ├── test_api_integration.py
│       │   └── test_rag_pipeline.py
│       │
│       ├── unit/                        # tests unitaires par module
│       │   ├── test_api.py
│       │   ├── test_data_utils.py
│       │   ├── test_embeddings.py
│       │   ├── test_llm.py
│       │   └── test_vector_store.py
│       │
│       └── tests_results/               # captures et logs des tests automatisés
│           ├── collected_data_stats.png
│           ├── data_utils_tests_screenshot.png
│           ├── embeddings_tests_screenshots.png
│           ├── llm_tests_screenshot.png
│           ├── rag_pipeline_test_screenshot.png
│           ├── tests.log
│           ├── vector_store_index_screenshot.png
│           └── vector_store_tests_screenshots.png
│
├── frontend/                            # interface web (client)
│   ├── index.html                       # page principale
│   ├── app.js                           # logique front-end
│   ├── style.css                        # styles de l’interface
│   └── logo.jpg                         # logo du projet
│
├── logs/                                # répertoire des journaux (non versionné)
│
├── research/                            # espace de recherche / expérimentations et notebooks
│
├── src/                                 # code source principal du backend et du pipeline RAG
│   ├── core/                            # configuration globale et constantes
│   │   └── config.py
│   │
│   ├── data_collection/                 # scripts de collecte des données initiales
│   │   └── tropical_medical_data_collector.py
│   │
│   ├── rag_pipeline/                    # modules du pipeline RAG (embeddings, LLM, vector store, etc.)
│   │   ├── data_utils.py
│   │   ├── embeddings.py
│   │   ├── llm.py
│   │   ├── rag.py
│   │   └── vector_store.py
│   │
│   ├── scripts/                         # scripts utilitaires (indexation, maintenance, etc.)
│   │   └── store_index.py
│   │
│   └── server/                          # API backend (FastAPI ou équivalent)
│       ├── main.py                      # point d’entrée de l’API
│       ├── models.py                    # modèles Pydantic ou ORM
│       └── routes.py                    # définition des endpoints
│
├── LICENSE                              # licence du projet
|
├── Makefile                             # commandes automatisées (build, tests, etc.)
|
├── pytest.ini                           # configuration des tests Pytest
|
├── rapport.md                           # rapport de synthèse ou document final du projet
|
├── README.md                            # description du projet (vue d’ensemble)
|
└── requirements.txt                     # dépendances Python nécessaires

```

---

## Installation

### Prérequis

* Python **3.12+**, **Make**, 4 Go RAM mini
* Token HuggingFace dans `.env` → `HF_TOKEN=...`
* Connexion Internet (première installation uniquement)
* Conda (recommandé) **ou** venv (fallback pip)

### Installer Make (si absent)

**Linux (Debian/Ubuntu)**

```bash
sudo apt-get update && sudo apt-get install -y build-essential make
```

**macOS**

```bash
xcode-select --install   # Make via Command Line Tools
```

**Windows**

```bash
# Option A: via Chocolatey
choco install make
# Option B: via WSL (Ubuntu) puis utiliser la commande Linux ci‑dessus
# Option C: Git Bash (inclut souvent make)
```

### Mise en place et installation rapide avec Conda (recommandé)

```bash
git clone https://github.com/Y4NN777/tenglaafi.git
cd tenglaafi
conda create -n tenglaafi python=3.12 -y
conda activate tenglaafi
pip install -r requirements.txt
cp .env.example .env   # puis renseigner HF_TOKEN
make setup
make index              # indexe le corpus dans ChromaDB
make run                # lance l'API → http://localhost:8000
```

### Fallback sans Conda (venv + pip)

```bash
python -m venv venv
# Linux/Mac
source venv/bin/activate
# Windows
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # puis renseigner HF_TOKEN
make setup && make index && make run
```

### Vérification

```bash
curl http://localhost:8000/health
# {"status": "healthy", "documents_indexed": 1531}
```

---

## Commandes Make (principales)

```bash
make setup          # Config initiale (env, dossiers, etc.)
make collect        # (Optionnel) collecte/rafraîchissement des données
make index          # Indexer le corpus dans ChromaDB
make run            # Lancer le serveur FastAPI
make clean          # Nettoyage (artéfacts, caches)

# Tests
make test           # Tous les tests
make test-unit      # Tests unitaires
make test-integration  # Tests d'intégration

# Évaluation (20 questions)
make evaluate       # Génère JSON + CSV d’évaluation
```

---

## Évaluation (résumé)

* Dataset : **20 questions**
* Script : `evaluation/scripts/evaluate.py` (appelé via `make evaluate`)
* Sorties :

  * `evaluation/evaluation_results/evaluation_results.json`
  * `evaluation/evaluation_results/evaluation_results.csv`

**Scores moyens observés**

| Métrique              | Valeur         |
| --------------------- | -------------- |
| Précision Retrieval   | **0.4483**     |
| Complétude Réponse    | **0.4558**     |
| Similarité Sémantique | **0.607**      |
| Pertinence (/5)       | **≈ 2.73 / 5** |
| Temps de réponse      | **≈ 2.39 s**   |

> Analyse complète : `docs/EVALUATION.md`.

---

##  Signification du Nom

**TengLaafi** vient de deux mots en mooré :
- **Tenga** (🌍) : la terre, le territoire
- **Laafi** (💚) : la santé, le bien-être, la paix

- Ensemble, ces mots forment "TengLaafi" - *la santé enracinée dans la terre*. Ce nom symbolise une IA de santé ancrée dans les savoirs du Burkina, reliant la connaissance médicale moderne aux valeurs naturelles et culturelles locales.
---