"""
Module: vector_store
====================

Implémentation de la base vectorielle ChromaDB pour le pipeline RAG Tenglaafi.

Ce module encapsule l’accès à une base vectorielle persistante (ChromaDB) via une
API de haut niveau offrant :
  - Initialisation résiliente d’un client persistant et d’une collection.
  - Indexation par lots de documents + embeddings (ordonnancement garanti).
  - Recherche top-K par similarité vectorielle avec filtrage métadonnées.
  - Récupération ciblée par identifiant.
  - Opérations de maintenance (compter, vérification de santé, reset).

Dépendances:
    - chromadb (client persistant).
    - Configuration projet: CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME, LOGGING_CONFIG.

Invariants et garanties:
    - L’ordre des embeddings correspond à l’ordre des documents.
    - Les IDs indexés sont des chaînes (casting de int -> str géré à l’écriture).
    - La persistance disque est assurée sous CHROMA_PERSIST_DIR.
    - Les erreurs par lot n’interrompent pas l’indexation totale (log + continue).

Classe
------
class ChromaVectorStore:
    Gestionnaire de base vectorielle ChromaDB

    __init__(persist_dir: str = CHROMA_PERSIST_DIR,
             collection_name: str = CHROMA_COLLECTION_NAME)
        Initialise un client persistant pointant vers `persist_dir` (création
        du répertoire si nécessaire). Récupère ou crée la collection `collection_name`
        (jusqu’à 3 tentatives avec délai croissant). Journalise succès/erreurs.

    index_documents(docs: List[Dict], embeddings: List[List[float]],
                    batch_size: int = 100) -> None
        Indexe des documents et leurs embeddings par tranches successives.
        Entrées attendues pour chaque document: "id", "title", "text".
        Métadonnées optionnelles: "url", "length", "source".
        En cas d’erreur de batch: log et poursuite de l’indexation suivante.

    search(query_embedding: List[float], k: int = 5,
           filter_metadata: Optional[Dict] = None) -> Dict
        Recherche top-K (similarité cosinus/HNSW côté Chroma).
        Retourne un dictionnaire:
            {
              "ids": List[int],
              "documents": List[str],
              "metadatas": List[dict],
              "distances": List[float]
            }
        Note: Chroma expose "distances" (plus petit = plus proche en cosine distance).

    get_document_by_id(doc_id: int) -> Optional[Dict]
        Récupère un document par identifiant (texte + métadonnées).
        Retourne None si l’ID n’existe pas.

    count_documents() -> int
        Retourne le nombre d’items indexés (0 en cas d’erreur).

    health_check() -> bool
        Vérifie l’accessibilité du store (true si OK, false sinon).
        Journalise le nombre courant de documents.

    delete_collection() -> None
        Supprime la collection active. À utiliser avant réindexation complète.

    reset() -> None
        Réinitialise la base: supprime la collection puis la recrée avec le nom
        par défaut CHROMA_COLLECTION_NAME.

Notes d’implémentation:
    - Journalisation: via LOGGING_CONFIG (dictConfig). Si votre LOGGING_CONFIG n’est
      pas au format dictConfig, adaptez l’initialisation du logging au niveau projet.
    - Robustesse: création des répertoires, retry à la création de collection,
      logs explicites sur les échecs de batch, et retour vide/0 en lecture en cas d’erreur.
    - Performance: indexation par lots (batch_size), appel unique à collection.add()
      par batch, métadonnées sérialisées en dict.
    - Compatibilité: fonctionne avec l’API moderne de Chroma (PersistentClient).

Exemple minimal:
    store = ChromaVectorStore()
    store.index_documents(docs, embeddings, batch_size=100)
    res = store.search(query_embedding, k=5, filter_metadata={"source": "WHO"})
    item = store.get_document_by_id(res["ids"][0]) if res["ids"] else None
    n = store.count_documents()
    ok = store.health_check()

Auteur : Y4NN777
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import logging
import logging.config
from pathlib import Path
from ..core.config import CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME, LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


class ChromaVectorStore:
    """Gestionnaire de base vectorielle ChromaDB"""
    
    def __init__(
        self, 
        persist_dir: str = CHROMA_PERSIST_DIR,
        collection_name: str = CHROMA_COLLECTION_NAME
    ):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # API MODERNE ChromaDB
        try:
            self.client = chromadb.PersistentClient(
                path=str(self.persist_dir)
            )
            logger.info(f"  ChromaDB initialisé: {self.persist_dir}")
        except Exception as e:
            logger.error(f"  Erreur connexion ChromaDB: {e}")
            raise
        
        # Création/récupération collection avec retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.collection = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata={"description": "Medical tropical diseases knowledge base"}
                )
                logger.info(f"  Collection '{collection_name}' prête")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"  Tentative {attempt+1}/{max_retries} échouée, retry...")
                    import time
                    time.sleep(2)
                else:
                    logger.error(f"  Échec création collection: {e}")
                    raise

    def index_documents(
        self,
        docs: List[Dict],
        embeddings: List[List[float]],
        batch_size: int = 100
    ) -> None:
        """
        Indexe des documents avec leurs embeddings
        
        Args:
            docs: Liste [{id, title, text, url}, ...]
            embeddings: Embeddings correspondants
            batch_size: Taille des lots
        """
        total = len(docs)
        logger.info(f"  Indexation de {total} documents...")
        
        for i in range(0, total, batch_size):
            batch_docs = docs[i:i+batch_size]
            batch_embeddings = embeddings[i:i+batch_size]
            
            try:
                ids = [str(doc["id"]) for doc in batch_docs]
                documents = [doc["text"] for doc in batch_docs]
                metadatas = [
                    {
                        "title": doc["title"],
                        "url": doc.get("url", ""),
                        "length": doc.get("length", 0),
                        "source": doc.get("source", "Unknown")
                    } 
                    for doc in batch_docs
                ]
                
                # Ajout avec gestion d'erreur
                self.collection.add(
                    ids=ids,
                    documents=documents,
                    embeddings=batch_embeddings,
                    metadatas=metadatas
                )
                
                logger.info(f"  Indexé {min(i+batch_size, total)}/{total}")
                
            except Exception as e:
                logger.error(f"  Erreur batch {i}-{i+batch_size}: {e}")
                # Continue avec le batch suivant
                continue
        
        logger.info("  Indexation terminée")
    
    def search(
        self,
        query_embedding: List[float],
        k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Recherche les documents les plus similaires
        
        Returns:
            {ids, documents, metadatas, distances}
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=filter_metadata
            )
            
            return {
                "ids": [int(id) for id in results["ids"][0]],
                "documents": results["documents"][0],
                "metadatas": results["metadatas"][0],
                "distances": results["distances"][0]
            }
        except Exception as e:
            logger.error(f"  Erreur recherche: {e}")
            return {"ids": [], "documents": [], "metadatas": [], "distances": []}
    
    def get_document_by_id(self, doc_id: int) -> Optional[Dict]:
        """Récupère un document par son ID"""
        try:
            result = self.collection.get(
                ids=[str(doc_id)],
                include=["documents", "metadatas"]
            )
            
            if result["ids"]:
                return {
                    "id": int(result["ids"][0]),
                    "text": result["documents"][0],
                    "metadata": result["metadatas"][0]
                }
        except Exception as e:
            logger.error(f"  Erreur récupération document {doc_id}: {e}")
        
        return None
    
    def count_documents(self) -> int:
        """Retourne le nombre de documents indexés"""
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"  Erreur count: {e}")
            return 0

    def health_check(self) -> bool:
        """Vérifie que ChromaDB est accessible"""
        try:
            count = self.count_documents()
            logger.info(f"  Health check OK: {count} documents")
            return True
        except Exception as e:
            logger.error(f"  Health check failed: {e}")
            return False
    
    def delete_collection(self):
        """Supprime la collection (pour réindexation)"""
        try:
            self.client.delete_collection(self.collection.name)
            logger.warning(f"  Collection '{self.collection.name}' supprimée")
        except Exception as e:
            logger.error(f"  Erreur suppression collection: {e}")
    
    def reset(self):
        """Réinitialise complètement la base"""
        try:
            self.delete_collection()
            self.collection = self.client.get_or_create_collection(
                name=CHROMA_COLLECTION_NAME
            )
            logger.info("  Base vectorielle réinitialisée")
        except Exception as e:
            logger.error(f"  Erreur reset: {e}")
            raise