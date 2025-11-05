"""
Client LLM open source (mode chat) pour le pipeline Tenglaafi.

Ce module implémente la classe `MedicalLLM`, un client universel pour les modèles
de langage hébergés sur Hugging Face Hub. Il est utilisé dans la phase de
génération du pipeline RAG pour produire des réponses contextualisées basées
sur des documents médicaux.

Fonctionnalités principales
---------------------------
- Compatibilité avec l’API Hugging Face Inference (mode conversationnel).
- Sélection automatique du modèle (`mistral`, `llama`, `meditron`).
- Gestion sécurisée du token Hugging Face (`HF_TOKEN`).
- Système de retry pour robustesse face aux erreurs réseau.
- Intégration transparente dans le pipeline RAG (via `get_llm_client()`).

Modèles recommandés
-------------------
- `mistralai/Mistral-7B-Instruct-v0.3`  → version utilisée par défaut.
- `meta-llama/Llama-2-7b-chat-hf`       → alternative open source.
- `epfl-llm/meditron-7b`                → modèle spécialisé dans le domaine médical.

Flux d’exécution
----------------
1. Initialisation du client Hugging Face Inference :
   - Chargement du modèle via `InferenceClient`.
   - Vérification automatique du token (`HF_TOKEN` ou variable d’environnement).
2. Construction du prompt conversationnel :
   - `system_prompt` : définit le rôle de l’assistant.
   - `user_prompt` : injecte le contexte et la question médicale.
3. Appel à l’API Hugging Face :
   - Mode récent → `client.chat_completions.create(...)`.
   - Mode ancien → `client.chat_completion(...)` (fallback rétrocompatible).
4. Retourne la réponse générée et nettoyée.

Composants exposés
------------------
- `MedicalLLM` : classe principale pour les appels LLM.
- `get_llm_client()` : singleton pour réutiliser le même client en mémoire.

Paramètres de configuration
----------------------------
- `HF_TOKEN` : clé d’accès Hugging Face (obligatoire pour les requêtes).
- `LLM_MODEL` : nom du modèle par défaut, issu de `src.core.config`.
- `LOGGING_CONFIG` : dictionnaire standard pour la configuration du logging.

Exemple d’utilisation
---------------------
    >>> from src.rag_pipeline.llm import get_llm_client
    >>> llm = get_llm_client("mistral")
    >>> answer = llm.generate_answer(
    ...     context=\"Le paludisme est causé par le parasite Plasmodium.\",
    ...     question=\"Quelle est la cause du paludisme ?\"
    ... )
    >>> print(answer)
    Le paludisme est provoqué par le parasite Plasmodium transmis par les moustiques Anopheles...

Bonnes pratiques
----------------
- Toujours définir le token Hugging Face (`export HF_TOKEN=...`).
- Utiliser la méthode `generate_answer()` au lieu d’appeler `_chat()` directement.
- Limiter `max_tokens` pour éviter les réponses trop longues.
- Utiliser `temperature=0.2` pour des réponses cohérentes et stables.
- En cas d’erreur ou de réponse trop courte, le système réessaie automatiquement (2 tentatives).

Auteur : Équipe Tenglaafi – Hackathon SN 2025
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
            import importlib

            hf_mod = importlib.import_module("huggingface_hub")
            InferenceClient = getattr(hf_mod, "InferenceClient")
        except Exception as e:
            logger.error("huggingface_hub non installé ou introuvable: %s", e)
            raise ImportError(
                "huggingface_hub est requis pour MedicalLLM; installez via `pip install huggingface-hub`"
            ) from e

        repo_id = self.MODELS.get(model_name, self.MODELS["mistral"])
        logger.info("Initialisation LLM (chat): %s", repo_id)

        self.model_id = repo_id
        self.client = InferenceClient(model=repo_id, token=hf_token)

        # Détection de l’API disponible (compat >=0.26 : chat_completions.create ; sinon chat_completion)
        self._use_chat_completions = hasattr(self.client, "chat_completions")

    def _chat(
        self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float
    ) -> str:
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
            "Tu es **Tenglaafi**, un assistant médical IA spécialisé dans les maladies tropicales "
            "et les plantes médicinales africaines. "
            "Ton rôle est d'aider les professionnels de santé et le grand public à comprendre, "
            "prévenir et traiter ces maladies à partir d’un corpus médical validé. "
            "Tu réponds **uniquement** en te basant sur le contexte fourni : "
            "si une information n’y figure pas, indique-le explicitement. "
            "Tu dois :\n"
            "1. Fournir des explications concises, factuelles et en français clair.\n"
            "2. Eviter d'inclure de citations comme [Document X] ou (Document Y) ou encore Document Z dans ta réponse générée. Les sources sont gérées séparément.\n"
            "3. Éviter toute spéculation ou hallucination.\n"
            "4. Employer un ton neutre, professionnel et bienveillant.\n"
            "5.Structurer la réponse en paragraphes ou listes pour la lisibilité."
        )

        user_prompt = (
            f" **Contexte médical disponible :**\n{context}\n\n"
            f" **Question :** {question}\n\n"
            " **Consigne :** Rédige une réponse claire et exacte, "
            "en citant les passages pertinents du contexte. "
            "Si tu n’as pas assez d’informations, indique-le explicitement "
            "plutôt que d’inventer une réponse."
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
