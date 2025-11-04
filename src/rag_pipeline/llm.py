"""
Client LLM open source via HuggingFace Inference API (mode chat)
"""
from typing import List, Dict, Optional
import os
import logging
import logging.config
from src.core.config import HF_TOKEN, LLM_MODEL, LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


class MedicalLLM:
    """Client LLM pour génération de réponses médicales via HuggingFace Inference (chat)"""

    # Modèles recommandés (open source)
    MODELS = {
        # Version exposée en conversational sur HF
        "mistral": "mistralai/Mistral-7B-Instruct-v0.3",
        # Alternatives: à utiliser si exposés en conversational
        "meditron": "epfl-llm/meditron-7b",
        # Llama 2 chat peut aussi être conversational
        "llama": "meta-llama/Llama-2-7b-chat-hf",
    }

    def __init__(self, model_name: str = "mistral", hf_token: Optional[str] = None):
        if not hf_token:
            hf_token = HF_TOKEN
            if not hf_token:
                raise ValueError(
                    "HF_TOKEN manquant ! Définir HF_TOKEN dans l'environnement "
                    "ou .env (https://huggingface.co/settings/tokens)."
                )

        try:
            from huggingface_hub import InferenceClient
        except Exception as e:
            logger.error("huggingface_hub non installé: %s", e)
            raise

        repo_id = self.MODELS.get(model_name, self.MODELS["mistral"])
        logger.info("Initialisation LLM (chat): %s", repo_id)

        self.model_id = repo_id
        self.client = InferenceClient(model=repo_id, token=hf_token)

        # Détection de l’API disponible (compat >=0.26 : chat_completions.create ; sinon chat_completion)
        self._use_chat_completions = hasattr(self.client, "chat_completions")

    def _chat(self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float) -> str:
        """Compat layer pour versions différentes de huggingface_hub."""
        if self._use_chat_completions:
            # API récente (client.chat_completions.create)
            resp = self.client.chat_completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return resp.choices[0].message.content
        else:
            # API plus ancienne (client.chat_completion)
            resp = self.client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            # structure légèrement différente
            return resp.choices[0].message.get("content", "").strip()

    def generate_answer(
        self,
        context: str,
        question: str,
        max_tokens: int = 512,
        temperature: float = 0.2,
    ) -> str:
        """
        Génère une réponse basée sur le contexte médical (mode chat, strictement contextuel).
        """
        system_prompt = (
            "Tu es Tenglaafi, un assistant médical IA spécialisé dans les maladies tropicales "
            "et les plantes médicinales. Tu réponds UNIQUEMENT en te basant sur le contexte fourni. "
            "Si l'information n'est pas dans le contexte, dis-le clairement. "
            "Cite toujours tes sources. Reste factuel et précis. Réponds en français."
        )

        user_prompt = (
            f"CONTEXTE MÉDICAL:\n{context}\n\n"
            f"QUESTION: {question}\n\n"
            "Consigne: Réponds clairement, cite les sources issues du contexte."
        )

        max_retries = 2
        for attempt in range(max_retries):
            try:
                answer = self._chat(system_prompt, user_prompt, max_tokens, temperature).strip()
                if len(answer) < 20:
                    logger.warning("Réponse trop courte (len=%d), retry...", len(answer))
                    continue
                return answer
            except Exception as e:
                logger.warning("Tentative %d échouée: %s", attempt + 1, e)
                if attempt + 1 >= max_retries:
                    logger.error("Echec génération après %d tentatives: %s", max_retries, e)

        return (
            "Désolé, une erreur s'est produite lors de la génération de la réponse. "
            "Veuillez réessayer dans quelques instants."
        )


# Singleton global
_llm_client = None

def get_llm_client(model_name: str = LLM_MODEL) -> MedicalLLM:
    """Récupère l'instance singleton du client LLM"""
    global _llm_client
    if _llm_client is None:
        _llm_client = MedicalLLM(model_name=model_name)
    return _llm_client
