#config.py
import os

class Config:
    """
    Configuration centrale du projet TengLaafi RAG.
    Gère les chemins, modèles et paramètres globaux.
    """

    # --- Dossiers ---
    DATA_PATH = os.getenv("DATA_PATH", "data/corpus.json")
    VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "data/vector_store")

    # --- Modèles ---
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    LLM_MODEL = os.getenv("LLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")

    # --- RAG parameters ---
    TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", 5))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", 512))

    # --- Autres paramètres ---
    DEBUG_MODE = bool(int(os.getenv("DEBUG_MODE", 1)))
