"""
Configuration centralisée des tests Pytest pour le projet Tenglaafi.

Ce fichier définit toutes les **fixtures partagées** et la configuration
globale des tests unitaires et d’intégration. Il garantit un environnement
de test cohérent, isolé et reproductible pour le pipeline RAG complet.

Fonctionnalités principales
---------------------------
1. **Fixtures de données**
   - `sample_corpus` : génère un corpus médical simulé de 10 documents.
   - `temp_corpus_file` : écrit ce corpus dans un fichier JSON temporaire.
   - `temp_chroma_dir` : crée un répertoire ChromaDB isolé pour les tests.

2. **Fixtures de composants**
   - `embedding_manager` : instance unique d’`EmbeddingManager` pour la session.
   - `vector_store` : crée une base Chroma temporaire pour chaque test, puis la réinitialise.
   - `llm_client` : client `MedicalLLM` avec gestion du token Hugging Face.
   - `rag_pipeline` : instancie un pipeline RAG complet (corpus, embeddings, LLM, Chroma)
     avec `force_reindex=True` pour des tests reproductibles.

3. **Fixtures API**
   - `api_client` : client `TestClient` (FastAPI) pour les tests d’API.
     Peut être activé en important `src.server.main:app`.

4. **Configuration des marqueurs Pytest**
   - `slow` : tests lents (>5 secondes).
   - `integration` : tests d’intégration end-to-end.
   - `requires_hf_token` : tests nécessitant un token Hugging Face.
   - `performance` : tests de charge ou de benchmark.

Utilisation typique
-------------------
Ces fixtures sont automatiquement injectées dans les tests selon leurs noms :
    def test_rag_query(rag_pipeline):
        answer, sources = rag_pipeline.query("Qu’est-ce que le paludisme ?")
        assert isinstance(answer, str)
        assert len(sources) > 0

Bonnes pratiques
----------------
- Ne pas modifier les chemins ou tokens directement dans les tests :
  centraliser ces changements ici pour cohérence.
- Conserver les fixtures **sans dépendance réseau** quand c’est possible
  (mocker les appels HTTP dans les tests unitaires).
- Nettoyer systématiquement les répertoires temporaires après chaque test.
- Garder une portée `session` pour les composants coûteux (embeddings, modèle).

Auteur : Y4NN777
"""

import pytest
import sys
from pathlib import Path
import tempfile
import json

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
            "source": "Test",
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
    store = ChromaVectorStore(persist_dir=str(temp_chroma_dir), collection_name="test_collection")
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
        corpus_path=str(temp_corpus_file), persist_dir=str(temp_chroma_dir), force_reindex=True
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
    config.addinivalue_line("markers", "slow: tests lents (>5s)")
    config.addinivalue_line("markers", "integration: tests d'intégration")
    config.addinivalue_line("markers", "requires_hf_token: nécessite HF_TOKEN")
    config.addinivalue_line("markers", "performance: tests de performance")
