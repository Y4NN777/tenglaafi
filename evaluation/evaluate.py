
"""Évaluation complète du pipeline RAG Tenglaafi.

Ce module orchestre l’évaluation automatique du pipeline RAG complet à partir
d’un jeu de questions standardisé (`evaluation/questions.json`), dans le cadre
du Hackathon Tenglaafi. Il exécute le pipeline pour chaque question, mesure les
temps de réponse, calcule des métriques d’évaluation et exporte les résultats.

------------------------------------------------------------------------------
1. OBJECTIF
------------------------------------------------------------------------------
Le but de ce script est de fournir une **évaluation reproductible et lisible**
des performances du système RAG sur un corpus médical tropical :

- Vérifier la **qualité du retrieval** (documents trouvés par ChromaDB)
- Évaluer la **pertinence de la génération** (réponses du LLM)
- Mesurer la **rapidité de réponse** du pipeline complet
- Consolider les **scores globaux** pour analyse ou annotation humaine

------------------------------------------------------------------------------
2. FLUX DE TRAVAIL
------------------------------------------------------------------------------
Pour chaque question du fichier `questions.json` :
  1. Exécution de `rag.query(question)` → obtention de `answer` et `sources`
  2. Calcul automatique de plusieurs métriques :
     - Précision du retrieval
     - Complétude de la réponse
     - Similarité sémantique (si SentenceTransformers disponible)
     - Temps de réponse
  3. Intégration facultative d’un score humain (`ratings.json`)
  4. Sauvegarde des résultats dans :
        - `evaluation/evaluation_results.json`
        - `evaluation/evaluation_results.csv`

------------------------------------------------------------------------------
3. MÉTRIQUES CALCULÉES
------------------------------------------------------------------------------
Les métriques sont fournies par `evaluation.metrics.RAGMetrics`, ou par un
calculateur de secours (`FallbackMetrics`) si la dépendance n’est pas disponible.

- **retrieval_precision** : proportion de mots-clés attendus retrouvés dans les
  textes des documents sources. Reflète la pertinence du moteur de recherche
  vectoriel ChromaDB.

- **answer_completeness** : proportion de mots-clés attendus réellement présents
  dans la réponse du modèle. Mesure la couverture de la question.

- **semantic_similarity** : (optionnelle) similarité cosinus entre la réponse
  générée et la réponse de référence via SentenceTransformers
  (`paraphrase-multilingual-mpnet-base-v2`).

- **response_time_sec** : temps de traitement complet de la requête, du LLM à
  la vectorisation.

------------------------------------------------------------------------------
4. STRUCTURE DES DONNÉES
------------------------------------------------------------------------------
Input :
    evaluation/questions.json
    [
      {
        "id": 1,
        "question": "Quels sont les symptômes du paludisme ?",
        "expected_answer": "Fièvre, frissons, céphalées...",
        "expected_keywords": ["fièvre", "frissons", "céphalées"]
      },
      ...
    ]

    evaluation/ratings.json (optionnel)
    [
      {"id": 1, "score": 4.5},
      {"id": 2, "score": 5.0}
    ]

Output :
    evaluation/evaluation_results.json
        {
          "summary": {...moyennes...},
          "results": [
            {
              "id": 1,
              "question": "...",
              "answer": "...",
              "metrics": {...}
            }
          ]
        }

    evaluation/evaluation_results.csv
        CSV plat avec colonnes :
        id | question | expected_answer | model_answer | retrieval_precision |
        semantic_similarity | answer_completeness | response_time_sec | human_rating

------------------------------------------------------------------------------
5. CLASSES ET FONCTIONS PRINCIPALES
------------------------------------------------------------------------------

`FallbackMetrics`
    Calculateur minimaliste utilisé si RAGMetrics n’est pas disponible.
    Fournit un calcul basique de la précision du retrieval et de la
    complétude de la réponse sans dépendances externes.

`run_evaluation(questions_path, ratings_path=None, out_json=None, out_csv=None)`
    Exécute le processus complet d’évaluation :
      - charge les questions
      - interroge le pipeline RAG
      - calcule les métriques
      - sauvegarde les résultats
    Renvoie un dictionnaire contenant `summary` et `results`.

------------------------------------------------------------------------------
6. EXÉCUTION
------------------------------------------------------------------------------
Depuis la racine du projet :
    make evaluate
ou :
    python evaluation/evaluation.py

Prérequis :
    - Corpus indexé (`make index`)
    - Fichier evaluation/questions.json disponible
    - Optionnel : ratings.json pour les notes humaines

------------------------------------------------------------------------------
7. EXEMPLE D’UTILISATION
------------------------------------------------------------------------------
>>> from pathlib import Path
>>> from evaluation.evaluation import run_evaluation
>>> payload = run_evaluation(
...     questions_path=Path("evaluation/questions.json"),
...     out_json=Path("evaluation/evaluation_results.json"),
...     out_csv=Path("evaluation/evaluation_results.csv")
... )
>>> print(payload["summary"])
{
    "retrieval_precision_avg": 0.68,
    "answer_completeness_avg": 0.59,
    "semantic_similarity_avg": 0.72,
    "response_time_avg_sec": 2.3
}

------------------------------------------------------------------------------
8. INTERPRÉTATION
------------------------------------------------------------------------------
- `retrieval_precision_avg` > 0.1 : le moteur Chroma arrive à retrouver bien les documents
- `answer_completeness_avg` > 0.5 : le LLM couvre l’essentiel du contexte
- `semantic_similarity_avg` > 0.7 : la réponse correspond à la référence
- `response_time_avg_sec` < 3.0 : pipeline fluide et performant

------------------------------------------------------------------------------
9. REMARQUES
------------------------------------------------------------------------------
- Le module fonctionne même sans dépendance externe (`sentence-transformers`).
- L’évaluation produit des scores objectifs ET interprétables.
- Les résultats peuvent être directement utilisés pour comparer plusieurs runs
  (avant/après optimisation du pipeline ou changement de modèle).
"""




from __future__ import annotations

import json
import csv
import statistics
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

# Rendre importable le code source et le package evaluation
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
EVAL = ROOT / "evaluation"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SRC))

# Pipeline RAG
from src.rag_pipeline.rag import get_rag_pipeline

# Métriques (avec fallback si l'implémentation locale diffère)
try:
    from evaluation.metrics import RAGMetrics  # type: ignore
except Exception:
    RAGMetrics = None  # fallback plus bas


class FallbackMetrics:
    """Calculateur de secours si `evaluation.metrics.RAGMetrics` n'est pas disponible.

    Implémente trois proxys simples :
      - retrieval_precision : part des documents dont le texte ou le titre contient
        au moins un mot-clé attendu
      - answer_completeness : part des mots-clés attendus présents dans la réponse
      - semantic_similarity : None (non calculée ici)
    """

    @staticmethod
    def _norm(s: str) -> str:
        return (s or "").lower()

    def evaluate_response(
        self,
        question: str,
        generated_answer: str,
        retrieved_docs: List[Dict[str, Any]] | None,
        reference_answer: Optional[str] = None,
        expected_keywords: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        expected_keywords = expected_keywords or []
        kws = [self._norm(k) for k in expected_keywords if k]

        # retrieval_precision proxy
        ret_docs = retrieved_docs or []
        if ret_docs and kws:
            matches = 0
            for d in ret_docs:
                txt = self._norm(str(d.get("text", "")))
                ttl = self._norm(str(d.get("title", "")))
                if any(k in txt or k in ttl for k in kws):
                    matches += 1
            retrieval_precision = matches / len(ret_docs)
        else:
            retrieval_precision = None

        # answer_completeness proxy
        ans = self._norm(generated_answer or "")
        if kws:
            covered = sum(1 for k in kws if k in ans)
            answer_completeness = covered / len(kws)
        else:
            answer_completeness = None

        return {
            "retrieval_precision": retrieval_precision,
            "answer_completeness": answer_completeness,
            "semantic_similarity": None,  # non calculé en fallback
        }


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_questions(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Fichier questions introuvable: {path}")
    data = load_json(path)
    if not isinstance(data, list):
        raise ValueError("questions.json doit contenir une liste d'objets question")
    return data


def load_ratings_optional(path: Path) -> Dict[int, float]:
    """Charge un ratings.json optionnel et renvoie un mapping id->score."""
    if not path.exists():
        return {}
    data = load_json(path)
    m: Dict[int, float] = {}
    for item in data:
        try:
            m[int(item["id"])] = float(item["score"])
        except Exception:
            continue
    return m


def mean_or_none(vals: List[Optional[float]]) -> Optional[float]:
    xs = [v for v in vals if isinstance(v, (int, float))]
    return round(statistics.mean(xs), 4) if xs else None


def run_evaluation(
    questions_path: Path,
    ratings_path: Optional[Path] = None,
    out_json: Optional[Path] = None,
    out_csv: Optional[Path] = None,
) -> Dict[str, Any]:
    questions = load_questions(questions_path)
    ratings = load_ratings_optional(ratings_path) if ratings_path else {}

    # Prépare pipeline
    rag = get_rag_pipeline(force_reload=False)

    # Choix du calculateur de métriques
    metrics_calc = None
    if RAGMetrics is not None:
        try:
            metrics_calc = RAGMetrics()
        except Exception:
            metrics_calc = None
    if metrics_calc is None:
        metrics_calc = FallbackMetrics()

    results: List[Dict[str, Any]] = []

    # Exécution question par question
    for q in questions:
        qid = int(q.get("id", -1))
        qtext: str = q.get("question", "")
        expected_answer: Optional[str] = q.get("expected_answer")
        expected_keywords: Optional[List[str]] = q.get("expected_keywords")

        t0 = time.perf_counter()
        answer, sources = rag.query(qtext, k=5, use_cache=False)
        dt = time.perf_counter() - t0

        metrics = metrics_calc.evaluate_response(
            question=qtext,
            generated_answer=answer,
            retrieved_docs=sources,
            reference_answer=expected_answer,
            expected_keywords=expected_keywords,
        )
        metrics["response_time"] = dt
        if qid in ratings:
            metrics["human_rating"] = ratings[qid]

        results.append(
            {
                "id": qid,
                "question": qtext,
                "expected_answer": expected_answer,
                "expected_keywords": expected_keywords,
                "answer": answer,
                "sources": sources,
                "metrics": metrics,
            }
        )

    # Agrégations
    summary = {
        "retrieval_precision_avg": mean_or_none([r["metrics"].get("retrieval_precision") for r in results]),
        "answer_completeness_avg": mean_or_none([r["metrics"].get("answer_completeness") for r in results]),
        "semantic_similarity_avg": mean_or_none([r["metrics"].get("semantic_similarity") for r in results]),
        "response_time_avg_sec": mean_or_none([r["metrics"].get("response_time") for r in results]),
        "human_rating_avg_5": mean_or_none([r["metrics"].get("human_rating") for r in results]),
        "num_questions": len(results),
    }

    payload = {"summary": summary, "results": results}

    # Export JSON
    if out_json is not None:
        out_json.parent.mkdir(parents=True, exist_ok=True)
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"Résultats JSON : {out_json}")

    # Export CSV (tableau plat)
    if out_csv is not None:
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        with open(out_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "id",
                    "question",
                    "expected_answer",
                    "expected_keywords",
                    "model_answer",
                    "retrieval_precision",
                    "semantic_similarity",
                    "answer_completeness",
                    "response_time_sec",
                    "human_rating",
                ]
            )
            for r in results:
                m = r["metrics"]
                writer.writerow(
                    [
                        r.get("id"),
                        r.get("question"),
                        r.get("expected_answer"),
                        ", ".join(r.get("expected_keywords") or []),
                        r.get("answer"),
                        m.get("retrieval_precision"),
                        m.get("semantic_similarity"),
                        m.get("answer_completeness"),
                        m.get("response_time"),
                        m.get("human_rating"),
                    ]
                )
        print(f"Résultats CSV  : {out_csv}")

    return payload


if __name__ == "__main__":
    questions_path = EVAL / "questions.json"
    ratings_path = EVAL / "ratings.json"  # optionnel
    out_json = EVAL / "evaluation_results.json"
    out_csv = EVAL / "evaluation_results.csv"

    print("\n=== Évaluation Tenglaafi (RAG) ===")
    print(f"Questions : {questions_path}")
    if ratings_path.exists():
        print(f"Notes humaines : {ratings_path}")
    else:
        print("Notes humaines : (aucune) — ratings.json non trouvé")

    summary = run_evaluation(
        questions_path=questions_path,
        ratings_path=ratings_path if ratings_path.exists() else None,
        out_json=out_json,
        out_csv=out_csv,
    )["summary"]

    print("\n--- Récapitulatif ---")
    if summary.get("retrieval_precision_avg") is not None:
        print(f"Précision retrieval moy. : {summary['retrieval_precision_avg']}")
    if summary.get("answer_completeness_avg") is not None:
        print(f"Complétude réponse moy. : {summary['answer_completeness_avg']}")
    if summary.get("semantic_similarity_avg") is not None:
        print(f"Similarité sémantique moy.: {summary['semantic_similarity_avg']}")
    if summary.get("human_rating_avg_5") is not None:
        print(f"Note humaine moy. (/5)  : {summary['human_rating_avg_5']}")
    if summary.get("response_time_avg_sec") is not None:
        print(f"Temps de réponse moy. (s): {summary['response_time_avg_sec']}")

    print("\nExport : evaluation_results.json + evaluation_results.csv")
