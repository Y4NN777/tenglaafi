"""
Module: embeddings
==================

Gestion des embeddings textuels pour le pipeline RAG Tenglaafi.

Ce module convertit des textes en représentations numériques (vecteurs d’embeddings)
afin de permettre la recherche sémantique entre questions et documents médicaux.
Il s’appuie sur la bibliothèque `SentenceTransformers` pour générer des embeddings
normalisés utilisables dans une base vectorielle (ChromaDB).

───────────────────────────────────────────────────────────────
CLASSES ET MÉTHODES
───────────────────────────────────────────────────────────────

1. EmbeddingManager
-------------------
Classe principale assurant le chargement du modèle et le calcul des embeddings.

Méthodes :
    - __init__(model_name: str = EMBEDDING_MODEL)
        Initialise le modèle d’embedding spécifié dans la configuration.
        Récupère la dimension du vecteur et prépare le logger.

    - embed_texts(texts: List[str], batch_size: int = 32,
                  show_progress: bool = True) -> np.ndarray
        Calcule les embeddings pour une liste de textes.
        - Retour : tableau numpy de taille (n_texts, embedding_dim).

    - embed_query(query: str) -> np.ndarray
        Calcule l’embedding d’une requête unique.
        - Retour : vecteur 1D numpy représentant la requête normalisée.

    - compute_similarity(query_embedding: np.ndarray,
                         document_embeddings: np.ndarray) -> np.ndarray
        Calcule la similarité cosinus entre une requête et plusieurs documents.
        - Retour : tableau de scores de similarité (valeurs entre -1 et 1).

2. Fonctions globales utilitaires
---------------------------------
    - get_embedding_manager() -> EmbeddingManager
        Fournit une instance unique (singleton) du gestionnaire d’embeddings.
        Évite le rechargement multiple du modèle en mémoire.

    - embed_texts(texts: List[str]) -> List[List[float]]
        Interface simplifiée pour encoder une liste de textes sans instancier la classe.

    - embed_query(query: str) -> List[float]
        Interface simplifiée pour encoder une seule requête utilisateur.

───────────────────────────────────────────────────────────────
NOTES DE CONCEPTION
───────────────────────────────────────────────────────────────
- Utilise le modèle par défaut défini dans `src/core/config.py`
  (par ex. "sentence-transformers/paraphrase-multilingual-mpnet-base-v2").
- Tous les vecteurs sont normalisés pour des calculs de similarité fiables.
- Architecture stateless (singleton) pour limiter la charge mémoire.
- Journalisation conforme à la configuration globale LOGGING_CONFIG.

───────────────────────────────────────────────────────────────
INTÉGRATION DANS LE PIPELINE
───────────────────────────────────────────────────────────────
- Indexation : génération d’embeddings pour tous les documents du corpus.
- Recherche : génération d’un embedding de la requête utilisateur.
- Similarité : comparaison cosinus entre la requête et les embeddings stockés.

Auteur : Y4NN777
"""


from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np
import logging
from src.core.config import EMBEDDING_MODEL, LOGGING_CONFIG

logging.basicConfig(**LOGGING_CONFIG)
logger = logging.getLogger(__name__)


class EmbeddingManager:
    """
     Gestionnaire des embeddings avec cache et optimisations
    """
    
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        
        logger.info(f"  Chargement du modèle d'embeddings: {model_name}")
        
        try:
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"  Modèle chargé (dimension: {self.dimension})")
        except Exception as e:
            logger.error(f" Erreur chargement modèle: {e} ") 
            raise       
        
    
    def embed_texts(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> np.ndarray:
        
        """
        Calcule les embeddings pour une liste de textes
         
        Args:
            texts: List[str] : Listes de textes pour encodage
            batch_size: Taille des lots pour le traitement
            show_progress: Afficher la barre de progression
         
        Returns:
            Array numpy des embeddings

        """
        
        if not texts:
            return np.array([])
        
        try: 
            embeddings = self.model.encode(
               texts,
               batch_size=batch_size,
               show_progress_bar=show_progress,
               convert_to_numpy=True,
               normalize_embeddings=True
            )
            
            return embeddings
            
        except Exception as e:
            logger.error(f" Erreur génération embeddings: {e} ")
            raise
        
        
    def embed_query(self, query: str) -> np.ndarray:
        
        """
        Calcule l'embedding d'une requête unique
        
        Args:
            query: Texte de la requête
        
        Returns:
            Array numpy de l'embedding (1D)
        """
        
        if not query:
            return np.array([])
        
        try:
            embeding = self.model.encode(
              [query],
              convert_to_numpy=True,
              normalize_embeddings=True  
            )[0]
            
            return embeding            
        except Exception as e:
            logger.error(f"  Erreur embedding query: {e}")
            raise
        
        
    def compute_similarity(
        self,
        query_embedding: np.ndarray,
        document_embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Calcule la similarité cosinus entre une requête et des documents
        
        Args:
            query_embedding: Embedding de la requête (1D)
            document_embeddings: Embeddings des documents (2D)
        
        Returns:
            Scores de similarité
        """
        try:
            # Cosine similarity via produit scalaire (vecteurs normalisés)
            similarities = np.dot(document_embeddings, query_embedding)
            return similarities
        except Exception as e:
            logger.error(f"  Erreur calcul similarité: {e}")
            raise
        
# Singleton global
_embedding_manager = None

def get_embedding_manager() -> EmbeddingManager:
    """Récupère l'instance singleton du gestionnaire d'embeddings"""
    global _embedding_manager
    if _embedding_manager is None:
        _embedding_manager = EmbeddingManager()
    return _embedding_manager


# Utilitaires rapides pour acces direct sans instance de la classe

def embed_texts(texts: List[str]) -> List[List[float]]:
    """Calcul les embeddings de textes via le singleton pour une listes de textes"""
    embeddings = get_embedding_manager().embed_texts(texts)
    return embeddings.tolist()

def embed_query(query: str) -> List[float]:
    """Calcul l'embeddings d'une requête via le singleton"""
    embedding = get_embedding_manager().embed_query(query)
    return embedding.tolist()
