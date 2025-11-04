"""
Pipeline RAG complet orchestrant embeddings, base vectorielle (ChromaDB) et LLM.

Ce module définit la classe `RAGPipeline`, composant central du système Tenglaafi.
Il relie toutes les étapes du pipeline RAG (Retrieval-Augmented Generation) :
1. Chargement et validation du corpus local (JSON).
2. Génération d’embeddings (SentenceTransformers).
3. Indexation et recherche vectorielle (ChromaDB).
4. Génération de réponse contextuelle via un modèle LLM (Hugging Face / LangChain).
5. Mise en cache et gestion des requêtes en batch.

Fonctionnalités principales
---------------------------
- Réindexation conditionnelle : le pipeline ne reconstruit l’index que si le modèle
  d’embeddings ou le corpus ont changé (vérification via hash SHA-256 et métadonnées
  ChromaDB).
- Indexation optimisée : embeddings calculés par lot, ajoutés dans une collection
  persistante Chroma avec métadonnées complètes (titre, URL, source…).
- Requêtes sémantiques : recherche top-k des documents les plus proches d’une question
  utilisateur.
- Génération LLM : création de réponses contextualisées basées uniquement sur les
  documents retrouvés.
- Post-traitement : amélioration de la réponse avec un bloc “Sources consultées”.
- Cache mémoire : évite de recalculer les embeddings et requêtes répétées.
- Traitement batch : plusieurs questions traitées en série sans perte de contexte.

Paramètres de configuration
----------------------------
- `DATA_DIR` : répertoire contenant le corpus JSON (`data/corpus.json` par défaut).
- `CHROMA_PERSIST_DIR` : emplacement de la base vectorielle Chroma persistée.
- `TOP_K_DOCUMENTS` : nombre de documents à récupérer par requête.
- `EMBEDDING_MODEL` : modèle SentenceTransformers utilisé pour les vecteurs.
- `LOGGING_CONFIG` : dictionnaire global de configuration des logs.

Flux de travail général
------------------------
1. Initialisation du pipeline (`RAGPipeline(force_reindex=False)`).
2. Chargement du corpus et vérification de l’état de la base Chroma.
3. Réindexation automatique si nécessaire (changement de corpus ou modèle).
4. Appel `query(question)` → embeddings + recherche + génération.
5. Mise en cache et retour de la réponse accompagnée des sources.

Exemple d’utilisation
---------------------
    >>> from src.rag_pipeline.rag import RAGPipeline
    >>> rag = RAGPipeline(force_reindex=False)
    >>> answer, sources = rag.query("Quels sont les symptômes du paludisme ?", k=3)
    >>> print(answer)
    Les symptômes du paludisme incluent fièvre, fatigue, céphalées et sueurs...

Bonnes pratiques
----------------
- Exécuter une indexation complète (force_reindex=True) après modification du corpus
  ou du modèle d’embeddings.
- Laisser `force_reindex=False` pour les runs de production afin de réutiliser la
  base persistée.
- Surveiller les logs pour détecter les erreurs ChromaDB ou LLM.
- Limiter la taille du contexte (`max_length ≈ 3000`) pour réduire la latence du LLM.
"""

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging
import logging.config
from .embeddings import get_embedding_manager
from .vector_store import ChromaVectorStore
from .llm import get_llm_client
from ..core.config import DATA_DIR, CHROMA_PERSIST_DIR, TOP_K_DOCUMENTS
from src.core.config import EMBEDDING_MODEL 
from src.core.config import LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


class RAGPipeline:
    """Pipeline RAG complet pour Tenglaafi"""
    
    def __init__(
        self,
        corpus_path: str = None,
        persist_dir: str = CHROMA_PERSIST_DIR,
        force_reindex: bool = False
    ):
        # Cache simple en mémoire
        self._query_cache = {}
        self._cache_max_size = 100
        
        # Chemins
        self.corpus_path = Path(corpus_path or DATA_DIR / "corpus.json")
        
        # Composants
        self.embedding_manager = get_embedding_manager()
        self.vector_store = ChromaVectorStore(persist_dir=persist_dir)
        self.llm = get_llm_client()
        
        # Chargement du corpus
        self.docs = self._load_corpus()
        logger.info(f"  Corpus chargé: {len(self.docs)} documents")

        # Lecture état existant
        existing = self.vector_store.count_documents()
        meta = (getattr(self.vector_store.collection, "metadata", None) or {})
        same_model  = (meta.get("embedding_model") == EMBEDDING_MODEL)
        same_corpus = (meta.get("corpus_hash") == self._hash_corpus())

        # Décision
        if force_reindex or existing == 0 or not (same_model and same_corpus):
            logger.info("  Réindexation nécessaire")
            self.build_index()
            # maj métadonnées collection après succès
            try:
                if hasattr(self.vector_store.collection, "modify"):
                    self.vector_store.collection.modify(metadata={
                        **meta,
                        "embedding_model": EMBEDDING_MODEL,
                        "corpus_hash": self._hash_corpus(),
                    })
                else:
                    logger.warning("  Méthode 'modify' non supportée par cette version de ChromaDB")
            except Exception as e:
                logger.warning(f"  Impossible de mettre à jour les métadonnées collection: {e}")

            

    def _hash_corpus(self) -> str:
        h = hashlib.sha256()
        for d in self.docs:
            # choisis un ordre stable
            h.update(str(d.get("id")).encode())
            h.update((d.get("title","")).encode())
            h.update((d.get("text","")).encode())
        return h.hexdigest()

    
    def _load_corpus(self) -> List[Dict]:
        """Charge le corpus JSON"""
        if not self.corpus_path.exists():
            raise FileNotFoundError(f"Corpus introuvable: {self.corpus_path}")
        
        try:
            with open(self.corpus_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"  Erreur chargement corpus: {e}")
            raise
    
    def build_index(self) -> None:
        """Construit l'index vectoriel complet"""
        logger.info("  Construction de l'index vectoriel...")
        
        # Extraction des textes
        texts = [doc["text"] for doc in self.docs]
        
        # Génération des embeddings
        logger.info("  Génération des embeddings...")
        embeddings = self.embedding_manager.embed_texts(
            texts, 
            batch_size=32,
            show_progress=True
        )
        
        # Indexation dans Chroma
        logger.info("  Indexation dans ChromaDB...")
        self.vector_store.index_documents(
            docs=self.docs,
            embeddings=embeddings.tolist()
        )
        
        logger.info("  Index construit avec succès")
    
    def query(
        self, 
        question: str, 
        k: int = TOP_K_DOCUMENTS,
        return_sources: bool = True,
        use_cache: bool = True
    ) -> Tuple[str, Optional[List[Dict]]]:
        """
        Traite une question et retourne la réponse RAG
        
        Args:
            question: Question de l'utilisateur
            k: Nombre de documents à récupérer
            return_sources: Retourner les documents sources
            use_cache: Utiliser le cache
        
        Returns:
            Tuple (réponse, documents_sources)
        """
        
        # question vide => retour canonicalisé
        if not (question or "").strip():
            return ("Question vide.", []) if return_sources else ("Question vide.", None)

        
        # Génération clé de cache
        cache_key = hashlib.md5(f"{question.lower().strip()}_{k}".encode()).hexdigest()

        if use_cache and cache_key in self._query_cache:
            logger.info(" Cache hit")
            return self._query_cache[cache_key]


        # 1. Embedding de la question
        logger.debug(f" Question: {question}")
        query_embedding = self.embedding_manager.embed_query(question)
        


        
        # 2. Recherche vectorielle
        results = self.vector_store.search(
            query_embedding=query_embedding.tolist(),
            k=k
        )
        
        # 3. Récupération des documents complets
        retrieved_docs = []
        for doc_id, metadata, distance in zip(
            results["ids"],
            results["metadatas"],
            results["distances"]
        ):
            doc = next((d for d in self.docs if d["id"] == doc_id), None)
            if doc:
                retrieved_docs.append({
                    "id": doc_id,
                    "title": doc["title"],
                    "text": doc["text"],
                    "url": doc.get("url", ""),
                    "similarity": 1 - distance  # Distance -> Similarité
                })
        
        # 4. Construction du contexte
        context = self._build_context(retrieved_docs)
        
        # 5. Génération de la réponse
        answer = self.llm.generate_answer(context, question)
        
        # 6. Post-traitement de la réponse
        answer = self._enhance_answer(answer, retrieved_docs)

        result = (answer, retrieved_docs) if return_sources else (answer, None)
        
        if use_cache:
            if len(self._query_cache) >= self._cache_max_size:
                # Supprimer l'entrée la plus ancienne (FIFO simple)
                oldest_key = next(iter(self._query_cache))
                del self._query_cache[oldest_key]
            
            self._query_cache[cache_key] = result
            logger.debug(f" Cached query (total: {len(self._query_cache)})")
        
        return result
    
    def clear_cache(self):
        """Vide le cache de requêtes"""
        self._query_cache.clear()
        logger.info(" Cache cleared")
    
    def _build_context(self, docs: List[Dict], max_length: int = 3000) -> str:
        """
        Construit le contexte à partir des documents récupérés
        
        Args:
            docs: Documents récupérés
            max_length: Longueur maximale du contexte (caractères)
        
        Returns:
            Contexte formaté
        """
        context_parts = []
        current_length = 0
        
        for doc in docs:
            # Format: [ID] Titre (Similarité: XX%) : Extrait
            doc_text = str(doc.get("text", ""))[:800]# Limite par document
            similarity_pct = int(doc["similarity"] * 100)
            
            part = (
                f"[Document {doc['id']}] {doc['title']} "
                f"(Pertinence: {similarity_pct}%)\n{doc_text}\n"
            )
            
            if current_length + len(part) > max_length:
                break
            
            context_parts.append(part)
            current_length += len(part)
        
        return "\n---\n".join(context_parts)
    
    def _enhance_answer(self, answer: str, sources: List[Dict]) -> str:
        """
        Améliore la réponse en ajoutant des références
        
        Args:
            answer: Réponse brute du LLM
            sources: Documents sources utilisés
        
        Returns:
            Réponse améliorée
        """
        
        if not answer:
            return "Aucune réponse générée (erreur LLM ou contexte vide)."
        
        # Vérification de citations existantes
        has_citations = any(f"[Document {doc['id']}]" in answer for doc in sources)
        

        if not has_citations and sources:
            # Ajout automatique des sources
            answer += "\n\n**Sources consultées:**\n"
            for doc in sources[:3]:  # Top 3 sources
                similarity = int(doc["similarity"] * 100)
                answer += f"- [{doc['id']}] {doc['title']} (Pertinence: {similarity}%)\n"
        
        return answer
    
    def batch_query(
        self,
        questions: List[str],
        k: int = TOP_K_DOCUMENTS,
        return_sources: bool = True,
        use_cache: bool = True,
    ) -> List[Dict]:
        """
        Traite plusieurs questions en batch en appelant `query` pour chacune.

        Args:
            questions: Liste de questions (str).
            k: Nombre de documents à récupérer (propagé à `query`).
            return_sources: Retourner les documents sources (propagé à `query`).
            use_cache: Utiliser le cache (propagé à `query`).

        Returns:
            Liste de résultats: [{"question", "answer", "sources"}]
        """
        # Validation d'entrée explicite (meilleur message d'erreur)
        if not isinstance(questions, (list, tuple)):
            raise TypeError("batch_query: 'questions' must be a list or tuple of strings")
        if any(not isinstance(q, str) for q in questions):
            raise TypeError("batch_query: each question must be a string")

        results: List[Dict] = []

        for q in questions:
            try:
                answer, sources = self.query(
                    q,
                    k=k,
                    return_sources=return_sources,
                    use_cache=use_cache,
                )
            except Exception as e:
                # Isolation des erreurs par question (ne casse pas tout le batch)
                answer = f"Erreur lors du traitement de la question: {e}"
                sources = [] if return_sources else None

            results.append({
                "question": q,
                "answer": answer,
                "sources": sources,
            })

        return results

    
    def get_similar_questions(self, question: str, k: int = 5) -> List[str]:
        """
        Trouve des questions similaires dans le corpus
        
        Args:
            question: Question de référence
            k: Nombre de suggestions
        
        Returns:
            Liste de titres de documents similaires
        """
        query_embedding = self.embedding_manager.embed_query(question)
        results = self.vector_store.search(query_embedding.tolist(), k=k)
        
        suggestions = [
            f"En savoir plus sur: {meta['title']}"
            for meta in results["metadatas"]
        ]
        
        return suggestions


# Singleton global
_rag_pipeline = None

def get_rag_pipeline(force_reload: bool = False) -> RAGPipeline:
    """Récupère l'instance singleton du pipeline RAG"""
    global _rag_pipeline
    if _rag_pipeline is None or force_reload:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline