"""
Métriques d'évaluation pragmatiques mais complètes pour pipeline RAG.

Ce module définit la classe `RAGMetrics`, un évaluateur simple et reproductible
pour juger la qualité d’un système RAG selon quatre axes principaux :

1) Similarité sémantique (optionnelle)
   - Compare la réponse générée à une réponse de référence en utilisant un
     modèle SentenceTransformers (par défaut :
     "sentence-transformers/paraphrase-multilingual-mpnet-base-v2").
   - Si `sentence-transformers` n’est pas installé ou le modèle indisponible,
     la métrique est omise (score 0.0 par défaut).

2) Précision du retrieval
   - Mesure la proportion de mots-clés attendus retrouvés dans les documents
     récupérés (concaténés). Les mots-clés sont normalisés (minuscules,
     accents supprimés) avant comparaison.

3) Complétude de la réponse
   - Mesure la proportion de mots-clés attendus présents dans la réponse
     générée (avec normalisation légère côté mots-clés).

4) Similarité moyenne des sources
   - Moyenne des champs "similarity" présents dans les documents renvoyés par
     la base vectorielle, en tant qu’indicateur global de pertinence retrieval.

Public API
----------
class RAGMetrics:
    __init__():
        Initialise les ressources d’évaluation. Tente de charger un modèle
        SentenceTransformers si disponible ; sinon, les métriques sémantiques
        sont désactivées en douceur.

    compute_semantic_similarity(generated_answer: str, reference_answer: str) -> float:
        Calcule une similarité sémantique (cosinus) entre la réponse générée et
        une réponse de référence. Retourne 0.0 si le modèle n’est pas chargé.

    compute_retrieval_precision(retrieved_docs: List[Dict], expected_keywords: List[str]) -> float:
        Évalue la présence des mots-clés attendus dans les textes concaténés des
        documents récupérés. Retourne un score entre 0 et 1.

    compute_answer_completeness(answer: str, expected_keywords: List[str]) -> float:
        Évalue la couverture des mots-clés attendus par la réponse générée.
        Retourne un score entre 0 et 1.

    compute_average_similarity(retrieved_docs: List[Dict]) -> float:
        Calcule la moyenne du champ "similarity" des documents récupérés.
        Retourne 0.0 si la liste est vide.

    evaluate_response(
        question: str,
        generated_answer: str,
        retrieved_docs: List[Dict],
        reference_answer: str | None = None,
        expected_keywords: List[str] | None = None
    ) -> Dict[str, float]:
        Calcule les métriques disponibles et retourne un dictionnaire de scores :
        {
            "answer_length": int,
            "num_sources": int,
            "avg_source_similarity": float,
            "retrieval_precision": float,        # si keywords fournis
            "answer_completeness": float,        # si keywords fournis
            "semantic_similarity": float         # si référence + modèle dispo
        }

Notes d’implémentation
----------------------
- La normalisation appliquée est volontairement simple et ciblée côté
  mots-clés (minuscules, accents supprimés, espaces réduits) afin d’être
  robuste aux variations typographiques fréquentes.
- La similarité sémantique peut entraîner un coût de calcul additionnel ; elle
  est optionnelle et se désactive automatiquement si les dépendances ne sont
  pas disponibles.
- Les métriques sont conçues pour être interprétables rapidement et corrélées
  aux exigences d’un hackathon (précision retrieval, complétude, temps, etc.).

Exemple minimal
---------------
>>> metrics = RAGMetrics()
>>> scores = metrics.evaluate_response(
...     question="Quels sont les symptômes du paludisme ?",
...     generated_answer="Fièvre, frissons, céphalées...",
...     retrieved_docs=[{"text": "La fièvre est fréquente...", "similarity": 0.72}],
...     reference_answer="Fièvre, frissons, céphalées, myalgies...",
...     expected_keywords=["fièvre", "frissons", "céphalées"]
... )
>>> sorted(scores.keys())
['answer_completeness', 'answer_length', 'avg_source_similarity',
 'num_sources', 'retrieval_precision', 'semantic_similarity']
 
Auteur : Y4NN777

"""

from typing import List, Dict
import numpy as np
import unicodedata
import re

try:
    from sentence_transformers import SentenceTransformer, util
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class RAGMetrics:
    """Métriques d'évaluation améliorées"""
    
    def __init__(self):
        # Modèle pour similarité sémantique
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.sentence_model = SentenceTransformer(
                    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
                )
            except Exception as e:
                print(f"  Erreur chargement modèle similarité: {e}")
                self.sentence_model = None
        else:
            self.sentence_model = None
    
    def compute_semantic_similarity(
        self, 
        generated_answer: str, 
        reference_answer: str
    ) -> float:
        """
        Similarité sémantique entre réponse générée et référence
        """
        if not self.sentence_model:
            return 0.0
            
        try:
            emb1 = self.sentence_model.encode(generated_answer, convert_to_tensor=True)
            emb2 = self.sentence_model.encode(reference_answer, convert_to_tensor=True)
            
            similarity = util.cos_sim(emb1, emb2).item()
            return similarity
        except Exception as e:
            print(f"  Erreur calcul similarité: {e}")
            return 0.0
    
    
    
    def _normalize(self, s: str) -> str:
        if not s:
            return ""
        s = s.lower()
        s = unicodedata.normalize("NFD", s)
        s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")  # strip accents
        s = re.sub(r"\s+", " ", s).strip()
        return s
    
    
    def compute_retrieval_precision(
        self,
        retrieved_docs: List[Dict],
        expected_keywords: List[str]
    ) -> float:
        """
        Précision du retrieval basée sur présence de keywords
        
        Args:
            retrieved_docs: Documents récupérés [{text, title}, ...]
            expected_keywords: Mots-clés attendus
        
        Returns:
            Score 0-1
        """
        if not retrieved_docs or not expected_keywords:
            return 0.0
        
        # Concaténation des textes
        all_text = " ".join([doc.get("text", "") for doc in retrieved_docs]).lower()

        keys = [self._normalize(kw) for kw in expected_keywords]

        # Comptage keywords présents
        found = sum(1 for kw in keys if kw in all_text)

        return found / len(expected_keywords)
    
    def compute_answer_completeness(
        self,
        answer: str,
        expected_keywords: List[str]
    ) -> float:
        """
        Complétude de la réponse
        
        Vérifie si la réponse couvre tous les aspects attendus
        """
        if not answer or not expected_keywords:
            return 0.0
            
        answer_lower = answer.lower()
        
        answers = [self._normalize(kw) for kw in expected_keywords]
        
        found = sum(1 for kw in answers if kw.lower() in answer_lower)
        
        return found / len(expected_keywords)
    
    def compute_average_similarity(self, retrieved_docs: List[Dict]) -> float:
        """
        Similarité moyenne des documents récupérés
        
        Indique la pertinence globale du retrieval
        """
        if not retrieved_docs:
            return 0.0
        
        similarities = [doc.get("similarity", 0.0) for doc in retrieved_docs]
        return np.mean(similarities)
    
    def evaluate_response(
        self,
        question: str,
        generated_answer: str,
        retrieved_docs: List[Dict],
        reference_answer: str = None,
        expected_keywords: List[str] = None
    ) -> Dict[str, float]:
        """
        Évaluation complète d'une réponse
        
        Returns:
            Dict avec toutes les métriques
        """
        metrics = {
            "answer_length": len(generated_answer),
            "num_sources": len(retrieved_docs),
            "avg_source_similarity": self.compute_average_similarity(retrieved_docs)
        }
        
        # Métriques basées sur keywords
        if expected_keywords:
            metrics["retrieval_precision"] = self.compute_retrieval_precision(
                retrieved_docs, expected_keywords
            )
            metrics["answer_completeness"] = self.compute_answer_completeness(
                generated_answer, expected_keywords
            )
        
        # Similarité sémantique (si référence disponible)
        if reference_answer and self.sentence_model:
            metrics["semantic_similarity"] = self.compute_semantic_similarity(
                generated_answer, reference_answer
            )
        
        return metrics