<<<<<<< HEAD
from dotenv import load_dotenv
import os

# Charger automatiquement les variables du fichier .env
load_dotenv()

class Settings:
    """Configuration centrale du backend TengLaafi"""
    APP_NAME = "TengLaafi API"
    APP_VERSION = "1.0.0"
    HF_TOKEN = os.getenv("HF_TOKEN")
    LLM_MODEL = os.getenv("LLM_MODEL", "mistral")
    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "tropical_medicine")
    ENV = os.getenv("ENV", "development")

# Instance unique (singleton)
settings = Settings()
=======
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Chemins
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma_db"
RESEARCH_DIR = BASE_DIR / "research"
LOG_FILE = BASE_DIR / "app.log"

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': str(LOG_FILE),
            'formatter': 'standard'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        }
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
}

# HuggingFace LLM (100% open source)
HF_TOKEN = os.getenv("HF_TOKEN")
LLM_MODEL = os.getenv("LLM_MODEL", "mistral")  # mistral|meditron|llama

# Configuration Embeddings (Amélioré pour médical)
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
EMBEDDING_DIMENSION = 768  # Plus riche que 384

# Configuration ChromaDB
CHROMA_COLLECTION_NAME = "tropical_medicine"
CHROMA_PERSIST_DIR = str(CHROMA_DIR)

# Configuration RAG (Chunking amélioré)
TOP_K_DOCUMENTS = 5
CHUNK_SIZE = 1000  # Augmenté pour contexte médical
CHUNK_OVERLAP = 200

# Configuration LLM
LLM_MAX_TOKENS = 512
LLM_TEMPERATURE = 0.2

# Configuration API
API_HOST = "0.0.0.0"
API_PORT = 8000
API_RELOAD = True

# Validation
if not HF_TOKEN:
    print("  HF_TOKEN manquant dans .env")
    print("Obtenez-le gratuitement sur https://huggingface.co/settings/tokens")
>>>>>>> 4b00721084952a5710bcb1bc9ee90cd2e9ee378d
