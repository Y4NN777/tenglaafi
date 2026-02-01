# TengLaafi - Conversational RAG Medical Assistant

**Specialized AI assistant for tropical diseases and African medicinal plants**

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-100%25%20Open%20Source-green.svg)](https://www.trychroma.com/)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Mistral%207B-yellow.svg)](https://huggingface.co)
[![LangChain](https://img.shields.io/badge/LangChain-orange.svg)](https://python.langchain.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## About This Project

TengLaafi began as a pre-qualifying submission for a hackathon focused on healthcare innovation in African contexts. Following its initial success, Y7 Labs has continued its development with significant enhancements in retrieval accuracy, response quality, and architectural robustness.

The system combines Retrieval-Augmented Generation (RAG) with a curated corpus of 1,531 medical documents to provide evidence-based responses about tropical diseases and traditional African medicinal plants. All user-facing content is delivered in French.

**TengLaafi** comes from two words in Mooré:
- **Tenga**: the earth, the territory
- **Laafi**: health, well-being, peace

Together, they form "TengLaafi" — health rooted in the land. This name embodies an AI health assistant anchored in Burkinabé knowledge, connecting modern medical research with local natural and cultural values.

---

## Project Rationale

**Domain:** Healthcare - Tropical Diseases and Medicinal Plants

**Justification:**
- **Local Relevance:** Burkina Faso is a tropical region with high prevalence of diseases such as malaria, dengue, and leishmaniasis
- **Information Gap:** Limited access to reliable medical information in French
- **Traditional Heritage:** Rich knowledge base of African medicinal plants (Artemisia, Neem, etc.)
- **Social Impact:** 24/7 accessible information system for awareness and prevention

---

## Technical Architecture

### Complete RAG Pipeline

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   User      │─────▶│  Embeddings  │─────▶│  ChromaDB   │
│  Question   │      │  (768-dim)   │      │  (Vector    │
└─────────────┘      └──────────────┘      │   Search)   │
                                           └──────┬──────┘
                                                  │
                                            Top-5 Documents
                                                  │
┌─────────────┐      ┌──────────────┐      ┌──────▼─────┐
│   Response  │◀─────│  HuggingFace │◀─────│  Context   │
│  + Sources  │      │     LLM      │      │  Builder   │
└─────────────┘      └──────────────┘      └────────────┘
```

### Technology Stack

#### LLM and Orchestration
| Component | Technology | Description |
|-----------|-------------|-------------|
| **LLM Model** | Mistral-7B-Instruct-v0.2 | Open-source LLM optimized for French |
| **LLM API** | HuggingFace Inference API | REST interface for LLM inference |
| **Orchestration** | LangChain | RAG framework for prompt chaining |

#### Database and Embeddings
| Component | Technology | Description |
|-----------|-------------|-------------|
| **Embeddings** | `paraphrase-multilingual-mpnet-base-v2` | Text to 768-dim vectors |
| **Vector Database** | ChromaDB 0.4.18 | Persistent vector storage with similarity search |

#### Backend and Frontend
| Component | Technology | Description |
|-----------|-------------|-------------|
| **Backend** | FastAPI | REST API with Pydantic validation |
| **Frontend** | TypeScript/Tailwind CSS | Responsive interface with conversation persistence |

### HuggingFace and LangChain Configuration

```python
# HuggingFace Configuration
MODELS = {
    "mistral": "mistralai/Mistral-7B-Instruct-v0.2",  # Primary model
    "llama": "meta-llama/Llama-2-7b-chat-hf",         # Alternative
    "meditron": "epfl-llm/meditron-7b"                # Medical specialist
}

# LangChain Configuration
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

**LLM Characteristics:**
- Model: Mistral-7B-Instruct (7 billion parameters)
- French Performance: Excellent French language support
- Context: 8k tokens (allows integration of multiple documents)
- Prompts: Instruction-optimized format

**LangChain Features:**
- Context and history management
- Automatic prompt formatting
- RAG component chaining
- Source tracking and citations

**Open Source Licenses:**
- ChromaDB: https://github.com/chroma-core/chroma/blob/main/LICENSE
- Sentence-Transformers: https://github.com/UKPLab/sentence-transformers/blob/master/LICENSE
- HuggingFace Transformers: https://github.com/huggingface/transformers/blob/main/LICENSE
- FastAPI: https://github.com/tiangolo/fastapi/blob/main/LICENSE
- LangChain: https://github.com/langchain-ai/langchain/blob/master/LICENSE
- Mistral-7B: https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2/blob/main/LICENSE
- MPNet: https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2/blob/main/LICENSE

---

## Data Corpus

### Sources (1,531 documents)

| Source | Count | Type | Description |
|--------|--------|------|-------------|
| **WHO** | 23 | Web scraping | Tropical disease factsheets |
| **PubMed** | 254 | Public API | Peer-reviewed scientific articles |
| **Local PDFs** | 1,243 | Documents | Medical guides, theses, reports |
| **Medicinal Plants** | 11 | Multi-source | Ethnobotanical databases |
| **TOTAL** | **1,531** | | **Validated corpus** |

**Delivered Files:**
- `data/corpus.json` - Structured corpus (1,531 documents)
- `data/sources.txt` - Complete URLs and references

### Covered Topics

- Malaria (Plasmodium, Anopheles, Artemisia)
- Dengue and hemorrhagic fevers
- Cutaneous/visceral leishmaniasis
- Schistosomiasis
- African medicinal plants (Neem, Moringa, etc.)
- Burkinabé traditional medicine

---

## Project Structure

```
.
├── chroma_db/                           # Persistent ChromaDB vector store
│
├── data/                                # Project datasets
│   ├── corpus.json                      # Consolidated RAG corpus
│   ├── sources.txt                      # Source reference list
│   └── raw/                             # Raw unprocessed data
│       ├── 2013_pharmacopee_des_plantes_medicinales_afrique_ouest.pdf
│       ├── african_traditional_medicine_e.pdf
│       └── oms_burkina_faso_bulletin_information_t2_2025.pdf
│
├── docs/                                # Technical and functional documentation
│   ├── API.md                           # API specification
│   ├── ARCHITECTURE.md                  # Technical architecture overview
│   ├── CONTRIBUTING.md                  # Contribution guidelines
│   └── EVALUATION.md                    # Evaluation methodology
│
├── evaluation/                          # Model evaluation scripts and results
│   ├── evaluation_results/              # Results (CSV, JSON)
│   │   ├── evaluation_results.csv
│   │   └── evaluation_results.json
│   ├── questions.json                   # 20 evaluation questions
│   ├── scripts/                         # Evaluation and metrics scripts
│   │   ├── evaluate.py
│   │   └── metrics.py
│   └── tests/                           # Unit and integration tests
│       ├── conftest.py                  # pytest configuration
│       ├── integration/                 # Integration tests
│       │   ├── test_api_integration.py
│       │   └── test_rag_pipeline.py
│       └── unit/                        # Unit tests by module
│           ├── test_api.py
│           ├── test_data_utils.py
│           ├── test_embeddings.py
│           ├── test_llm.py
│           └── test_vector_store.py
│
├── frontend/                            # Web interface (client)
│   ├── chat.html                        # Main chat interface
│   ├── index.html                       # Landing page
│   ├── landing.html                     # Alternative landing page
│   ├── app.ts                           # Main chat application logic
│   ├── session.ts                       # Session management (IndexedDB)
│   ├── types.ts                         # TypeScript interfaces
│   ├── style.css                        # Interface styles
│   └── logo.jpg                         # Project logo
│
├── src/                                 # Backend source code
│   ├── core/                            # Global configuration
│   │   └── config.py
│   ├── data_collection/                 # Data collection scripts
│   │   └── tropical_medical_data_collector.py
│   ├── rag_pipeline/                    # RAG pipeline modules
│   │   ├── data_utils.py
│   │   ├── embeddings.py
│   │   ├── llm.py
│   │   ├── rag.py
│   │   └── vector_store.py
│   ├── scripts/                         # Utility scripts
│   │   └── store_index.py
│   └── server/                          # FastAPI backend
│       ├── main.py                      # API entry point
│       ├── models.py                    # Pydantic models
│       └── routes.py                    # API endpoints
│
├── LICENSE                              # MIT License
├── Makefile                             # Automated commands
├── pytest.ini                           # pytest configuration
├── README.md                            # Project overview
└── requirements.txt                     # Python dependencies
```

---

## Installation

### Prerequisites

* Python 3.12+, Make, 4 GB RAM minimum
* HuggingFace token in `.env` → `HF_TOKEN=...`
* Internet connection (first installation only)
* Conda (recommended) or venv (fallback pip)

### Install Make (if absent)

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
# Option B: via WSL (Ubuntu) then use Linux command above
# Option C: Git Bash (often includes make)
```

### Quick Setup with Conda (Recommended)

```bash
git clone https://github.com/Y4NN777/tenglaafi.git
cd tenglaafi
conda create -n tenglaafi python=3.12 -y
conda activate tenglaafi
pip install -r requirements.txt
cp .env.example .env   # then add HF_TOKEN
make setup
make index              # Index corpus into ChromaDB
make run                # Launch API → http://localhost:8000
```

### Fallback without Conda (venv + pip)

```bash
python -m venv venv
# Linux/Mac
source venv/bin/activate
# Windows
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # then add HF_TOKEN
make setup && make index && make run
```

### Verification

```bash
curl http://localhost:8000/health
# {"status": "healthy", "documents_indexed": 1531}
```

---

## Key Commands (via Makefile)

```bash
make setup          # Initial configuration (env, directories, etc.)
make collect        # (Optional) Refresh/collect data
make index          # Index corpus into ChromaDB
make run            # Start FastAPI server
make clean          # Clean artifacts and caches

# Testing
make test           # All tests
make test-unit      # Unit tests only
make test-integration  # Integration tests only

# Evaluation (20 questions)
make evaluate       # Generate JSON + CSV evaluation results
```

---

## Evaluation Summary

* Dataset: 20 questions
* Script: `evaluation/scripts/evaluate.py` (invoked via `make evaluate`)
* Outputs:
  * `evaluation/evaluation_results/evaluation_results.json`
  * `evaluation/evaluation_results/evaluation_results.csv`

**Average Scores**

| Metric | Value |
| --------------------- | -------------- |
| Retrieval Precision | 0.4483 |
| Response Completeness | 0.4558 |
| Semantic Similarity | 0.607 |
| Relevance (/5) | ~2.73 / 5 |
| Response Time | ~2.39s |

Complete analysis: `docs/EVALUATION.md`

---

## Configuration

All environment variables are in `.env` (copy from `.env.example`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `HF_TOKEN` | — (required) | HuggingFace API token for LLM inference |
| `LLM_MODEL` | `HuggingFaceH4/zephyr-7b-alpha` | LLM model on HuggingFace Hub |
| `CHROMA_PERSIST_DIR` | `./chroma_db` | ChromaDB storage path |
| `CHROMA_COLLECTION_NAME` | `tropical_medicine` | ChromaDB collection name |
| `API_HOST` | `0.0.0.0` | FastAPI bind address |
| `API_PORT` | `8000` | FastAPI port |

Key constants in `src/core/config.py` (not env-overridable):
- `EMBEDDING_MODEL`: `paraphrase-multilingual-mpnet-base-v2`
- `EMBEDDING_DIMENSION`: 768
- `TOP_K_DOCUMENTS`: 5
- `CHUNK_SIZE`: 1000
- `CHUNK_OVERLAP`: 200
- `LLM_MAX_TOKENS`: 512
- `LLM_TEMPERATURE`: 0.2

---

## Corpus Format

`data/corpus.json` is a JSON array. Each entry:

```json
{
  "id": 123,
  "title": "Document title",
  "text": "Full document text...",
  "url": "https://source.url",
  "source": "WHO|PubMed|Local",
  "length": 2500,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

Minimum 500 documents required (enforced by validation).

---

## Testing Conventions

- Test root: `evaluation/tests/` (configured in `pytest.ini`)
- Mark integration tests: `@pytest.mark.integration`
- Mark slow tests: `@pytest.mark.slow`
- Run a single test file: `make individual-unit-test TEST=<path>`
- Or directly: `pytest evaluation/tests/unit/test_embeddings.py -v`

---

## Common Issues

- **"Index empty" on startup**: `chroma_db/` is empty or missing. Run `make index`.
- **HF_TOKEN missing**: `.env` file not created or token not set. Copy `.env.example` and add your token from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).
- **ChromaDB errors in tests**: Stale vector store. Delete `chroma_db/` and run `make index`.
- **Import errors**: Must run commands from the project root directory.
- **Changing the embedding model**: Update `EMBEDDING_MODEL` and `EMBEDDING_DIMENSION` in `src/core/config.py`, then run `make reindex`.

---

## Contributing

Contributions are welcome. See `docs/CONTRIBUTING.md` for guidelines.

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Contact

- **Developer:** Y4NN777
- **GitHub:** [github.com/Y4NN777/tenglaafi](https://github.com/Y4NN777/tenglaafi)
- **Email:** y4nn.dev@gmail.com
- **Project URL:** [y7labs.studio/tenglaafi](https://y7labs.studio/tenglaafi)
- **Organization:** Y7 Labs

---

## Acknowledgments

This project was initially developed as a pre-qualifying submission for a healthcare innovation hackathon. Y7 Labs has continued its development with enhanced retrieval mechanisms, improved response generation, and architectural refinements.

Special thanks to the open-source community for the foundational technologies that make this project possible.

---

**TengLaafi** - Health rooted in the land.
