"""
Module: store_index
===================

Script de ligne de commande pour indexer le corpus Tenglaafi dans la base vectorielle **ChromaDB**.

Ce module constitue la passerelle entre les données brutes collectées (fichier `corpus.json`)
et la base vectorielle utilisée par le pipeline RAG (`RAGPipeline`).
Il assure les étapes de vérification du corpus, d’affichage de statistiques et d’indexation complète.

Étapes principales :
    1. Chargement de la configuration d’environnement (.env) et des dépendances.
    2. Vérification de la présence du corpus JSON dans `DATA_DIR`.
    3. Calcul de statistiques globales : nombre de documents, taille totale et moyenne.
    4. Avertissement si le corpus contient moins de 500 documents (objectif hackathon).
    5. Initialisation du pipeline RAG et indexation complète dans ChromaDB.
    6. Test rapide de requête pour validation de l’indexation.

Entrées :
    - Fichier `corpus.json` dans `DATA_DIR`, contenant une liste de documents :
      {
          "id": int,
          "title": str,
          "text": str,
          "url": str,
          "source": str
      }

Sorties :
    - Base vectorielle ChromaDB persistée dans le répertoire configuré (`CHROMA_PERSIST_DIR`).
    - Résumé de l’opération imprimé en console.

Notes :
    - Le script doit être exécuté après la phase de collecte (`tropical_medical_data_collector.py`).
    - Si `corpus.json` est absent, le script s’interrompt proprement.
    - L’indexation peut être relancée avec l’argument `force_reindex=True`.

Exécution :
    python store_index.py

Exemple de sortie :
    ============================================================
      INDEXATION DU CORPUS TENGLAAFI
    ============================================================
      Documents: 512
      Caractères totaux: 1,341,950
      Longueur moyenne: 1575
      Indexation terminée!
      Documents indexés: 512
      Dimension embeddings: 768
      INDEXATION RÉUSSIE
    ============================================================

Auteur : Y4NN777
"""


from dotenv import load_dotenv
import sys
from pathlib import Path

# Configuration
load_dotenv()
sys.path.append(str(Path(__file__).parent))

from src.rag_pipeline.rag import RAGPipeline
from src.core.config import DATA_DIR


def main():
    print("=" * 60)
    print("  INDEXATION DU CORPUS TENGLAAFI")
    print("=" * 60)

    # Vérification du corpus
    corpus_path = DATA_DIR / "corpus.json"

    if not corpus_path.exists():
        print("  Corpus introuvable!")
        print(f"   Chemin attendu: {corpus_path}")
        print(
            "  Lancez d'abord: python src/data_collection/tropical_medical_data_collector.py"
        )
        return

    # Statistiques du corpus
    import json

    with open(corpus_path, encoding="utf-8") as f:
        corpus = json.load(f)

    stats = {
        "total_documents": len(corpus),
        "total_characters": sum(len(doc.get("text", "")) for doc in corpus),
        "avg_length": (
            sum(len(doc.get("text", "")) for doc in corpus) / len(corpus)
            if corpus
            else 0
        ),
    }

    print(f"\n  Statistiques du corpus:")
    print(f"   Documents: {stats['total_documents']}")
    print(f"   Caractères totaux: {stats['total_characters']:,}")
    print(f"   Longueur moyenne: {stats['avg_length']:.0f}")

    # Vérification objectif 500 documents
    if stats["total_documents"] < 500:
        print(f"\n  Attention: Seulement {stats['total_documents']} documents")
        print(f"   Objectif hackathon: 500 documents minimum")
        response = input("\nContinuer l'indexation? (o/n): ")
        if response.lower() != "o":
            return

    # Indexation
    print("\n  Démarrage de l'indexation...")
    rag = RAGPipeline(corpus_path=corpus_path, force_reindex=False)

    print(f"\n  Indexation terminée!")
    print(f"   Documents indexés: {rag.vector_store.count_documents()}")
    print(f"   Dimension embeddings: {rag.embedding_manager.dimension}")

    # Test rapide
    print("\n Test rapide du système...")
    test_question = "Quels sont les symptômes du paludisme?"
    answer, sources = rag.query(test_question, k=3)

    print(f"\n Question test: {test_question}")
    print(f" Réponse: {answer[:200]}...")
    print(f"  Sources récupérées: {len(sources)}")

    print("\n" + "=" * 60)
    print("  INDEXATION RÉUSSIE")
    print("=" * 60)


if __name__ == "__main__":
    main()
