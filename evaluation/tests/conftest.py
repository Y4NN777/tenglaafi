"""
evaluation/tests/conftest.py
Fixtures pytest partagées pour tous les tests - 
"""
import pytest
import sys
from pathlib import Path
import tempfile
import json

# Ajouter src au path - ADAPTÉ À LA NOUVELLE STRUCTURE
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.core.config import DATA_DIR, CHROMA_DIR
from src.rag_pipeline.embeddings import EmbeddingManager
from src.rag_pipeline.vector_store import ChromaVectorStore
from src.rag_pipeline.llm import MedicalLLM
from src.rag_pipeline.rag import RAGPipeline


# === FIXTURES DE DONNÉES ===

@pytest.fixture(scope="session")
def sample_corpus():
    """Corpus de test minimal (10 documents)"""
    return [
        {
            "id": i,
            "title": f"Document Test {i}",
            "text": f"Contenu médical test numéro {i}. " * 50,
            "url": f"https://test.com/doc{i}",
            "length": 500,
            "source": "Test"
        }
        for i in range(10)
    ]


@pytest.fixture(scope="session")
def temp_corpus_file(sample_corpus, tmp_path_factory):
    """Fichier corpus.json temporaire"""
    temp_dir = tmp_path_factory.mktemp("data")
    corpus_path = temp_dir / "corpus.json"
    
    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump(sample_corpus, f, ensure_ascii=False, indent=2)
    
    return corpus_path


@pytest.fixture(scope="session")
def temp_chroma_dir(tmp_path_factory):
    """Répertoire ChromaDB temporaire"""
    return tmp_path_factory.mktemp("chroma_test")


# === FIXTURES DE COMPOSANTS ===

@pytest.fixture(scope="session")
def embedding_manager():
    """Gestionnaire d'embeddings réutilisable"""
    return EmbeddingManager()


@pytest.fixture
def vector_store(temp_chroma_dir):
    """ChromaDB temporaire pour chaque test"""
    store = ChromaVectorStore(
        persist_dir=str(temp_chroma_dir),
        collection_name="test_collection"
    )
    yield store
    # Cleanup après le test
    try:
        store.reset()
    except:
        pass


@pytest.fixture
def llm_client():
    """Client LLM (mock si pas de token HF)"""
    try:
        return MedicalLLM(model_name="mistral")
    except ValueError:
        # Mock si pas de HF_TOKEN
        pytest.skip("HF_TOKEN requis pour tests LLM")


@pytest.fixture
def rag_pipeline(temp_corpus_file, temp_chroma_dir):
    """Pipeline RAG complet pour tests"""
    pipeline = RAGPipeline(
        corpus_path=str(temp_corpus_file),
        persist_dir=str(temp_chroma_dir),
        force_reindex=True
    )
    yield pipeline
    # Cleanup
    try:
        pipeline.vector_store.reset()
    except:
        pass


# === FIXTURES API ===

@pytest.fixture
def api_client():
    """Client de test FastAPI"""
    from fastapi.testclient import TestClient
    # from src.server.main import app
    # return TestClient(app)


# === MARKERS PYTEST ===

def pytest_configure(config):
    """Configuration des markers personnalisés"""
    config.addinivalue_line(
        "markers", "slow: tests lents (>5s)"
    )
    config.addinivalue_line(
        "markers", "integration: tests d'intégration"
    )
    config.addinivalue_line(
        "markers", "requires_hf_token: nécessite HF_TOKEN"
    )
    config.addinivalue_line(
        "markers", "performance: tests de performance"
    )