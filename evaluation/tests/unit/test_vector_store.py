"""
Tests unitaires pour ChromaDB vector store -
"""

import pytest
from src.rag_pipeline.vector_store import ChromaVectorStore


class TestChromaVectorStore:
    """Tests pour ChromaVectorStore"""

    def test_initialization(self, vector_store):
        """Test initialisation ChromaDB"""
        assert vector_store is not None
        assert vector_store.client is not None
        assert vector_store.collection is not None

    def test_count_documents_initially_zero(self, vector_store):
        """Test comptage initial de documents"""
        count = vector_store.count_documents()
        assert count == 0

    def test_index_documents(self, vector_store, sample_corpus, embedding_manager):
        """Test indexation de documents"""
        # Génération embeddings
        texts = [doc["text"] for doc in sample_corpus]
        embeddings = embedding_manager.embed_texts(texts, show_progress=False)

        # Indexation
        vector_store.index_documents(
            docs=sample_corpus, embeddings=embeddings.tolist(), batch_size=5
        )

        # Vérification
        count = vector_store.count_documents()
        assert count == len(sample_corpus)

    def test_search_returns_results(self, vector_store, sample_corpus, embedding_manager):
        """Test recherche retourne résultats"""
        # Indexation d'abord
        texts = [doc["text"] for doc in sample_corpus]
        embeddings = embedding_manager.embed_texts(texts, show_progress=False)
        vector_store.index_documents(sample_corpus, embeddings.tolist())

        # Recherche
        query_emb = embedding_manager.embed_query("test médical")
        results = vector_store.search(query_emb.tolist(), k=3)

        assert len(results["ids"]) <= 3
        assert len(results["documents"]) == len(results["ids"])
        assert len(results["metadatas"]) == len(results["ids"])

    def test_get_document_by_id(self, vector_store, sample_corpus, embedding_manager):
        """Test récupération document par ID"""
        # Indexation
        texts = [doc["text"] for doc in sample_corpus]
        embeddings = embedding_manager.embed_texts(texts, show_progress=False)
        vector_store.index_documents(sample_corpus, embeddings.tolist())

        # Récupération
        doc = vector_store.get_document_by_id(0)

        assert doc is not None
        assert doc["id"] == 0
        assert "text" in doc

    def test_health_check(self, vector_store):
        """Test health check"""
        is_healthy = vector_store.health_check()
        assert is_healthy is True
