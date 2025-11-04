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
