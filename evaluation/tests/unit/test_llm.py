"""
Tests unitaires pour LLM client - 
"""
import pytest
from src.rag_pipeline.llm import MedicalLLM


class TestMedicalLLM:
    """Tests pour MedicalLLM"""
    
    @pytest.mark.requires_hf_token
    def test_initialization(self, llm_client):
        """Test initialisation LLM"""
        assert llm_client is not None
        assert llm_client.client is not None
    
    @pytest.mark.requires_hf_token
    @pytest.mark.slow
    def test_generate_answer_returns_string(self, llm_client):
        """Test génération retourne string"""
        context = "Le paludisme est causé par Plasmodium."
        question = "Quelle est la cause du paludisme?"
        
        answer = llm_client.generate_answer(context, question)
        
        assert isinstance(answer, str)
        assert len(answer) > 0
    
    @pytest.mark.requires_hf_token
    @pytest.mark.slow
    def test_generate_answer_uses_context(self, llm_client):
        """Test que la réponse utilise le contexte"""
        context = "L'artemisia est utilisée contre le paludisme."
        question = "Quelle plante traite le paludisme?"
        
        answer = llm_client.generate_answer(context, question)
        
        # La réponse devrait mentionner artemisia
        assert any(k in answer.lower() for k in ["artemisia", "artémisia", "plante", "phytothérapie"])
    
def test_initialization_fails_without_token(monkeypatch):
    import sys
    import importlib
    import src.core.config as cfg

    # 1) Vider la source du token à la fois dans l'env et dans la config importée
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.setattr(cfg, "HF_TOKEN", "", raising=False)

    # 2) Purger le module pour forcer la ré-importation avec la nouvelle config
    sys.modules.pop("src.rag_pipeline.llm", None)

    # 3) Réimporter le module après patch
    import src.rag_pipeline.llm as llm
    importlib.reload(llm)

    # 4) Vérifier que l'init sans token lève bien l'erreur
    with pytest.raises(ValueError, match="HF_TOKEN"):
        llm.MedicalLLM()
