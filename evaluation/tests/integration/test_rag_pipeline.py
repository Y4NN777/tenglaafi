"""
Tests d'intégration du pipeline RAG complet - 
"""
import pytest
import time

from src import rag_pipeline


@pytest.mark.integration
class TestRAGPipelineIntegration:
    """Tests d'intégration du pipeline RAG"""
    
    def test_full_pipeline_initialization(self, rag_pipeline):
        """Test initialisation complète du pipeline"""
        assert rag_pipeline.docs is not None
        assert len(rag_pipeline.docs) > 0
        assert rag_pipeline.vector_store.count_documents() > 0
    
    @pytest.mark.slow
    @pytest.mark.requires_hf_token
    def test_end_to_end_query(self, rag_pipeline):
        question = "Qu'est-ce qu'un test médical?"
        start = time.time()
        answer, sources = rag_pipeline.query(question, k=3)
        duration = time.time() - start

        assert isinstance(answer, str) and len(answer) > 20
        assert isinstance(sources, list) and len(sources) <= 3
        assert all("id" in src and "similarity" in src for src in sources)

        # Seuil un peu plus large pour limiter la flakiness réseau/provider
        assert duration < 20.0, f"Trop lent: {duration:.2f}s"

    def test_cache_functionality(self, rag_pipeline):
        question = "Test cache question unique"

        start1 = time.time()
        answer1, sources1 = rag_pipeline.query(question, use_cache=True)
        time1 = time.time() - start1

        start2 = time.time()
        answer2, sources2 = rag_pipeline.query(question, use_cache=True)
        time2 = time.time() - start2

        # Cache: combine seuil relatif + absolu
        assert time2 < min(0.2 * time1, 0.2), f"Cache inefficace: {time1:.3f}s vs {time2:.3f}s"
        assert answer1 == answer2

    def test_batch_query(self, rag_pipeline):
        questions = ["Question test 1?", "Question test 2?", "Question test 3?"]
        results = rag_pipeline.batch_query(questions)

        assert len(results) == len(questions)
        assert all("answer" in r and "sources" in r for r in results)
        assert all(isinstance(r["answer"], str) and len(r["answer"]) > 0 for r in results)
        assert all(isinstance(r["sources"], list) for r in results)

    def test_empty_question_quick(self, rag_pipeline):
        ans, src = rag_pipeline.query("", k=3, use_cache=False)
        assert ans.startswith("Question vide.")
        assert src == []


        results = rag_pipeline.batch_query([""], k=3, return_sources=True, use_cache=False)
        assert len(results) == 1
        assert "answer" in results[0]
        assert "sources" in results[0]