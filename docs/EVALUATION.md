# Évaluation du pipeline RAG du chatbot Tenglaafi

## 1. Objectif général

Cette phase d'évaluation vise à mesurer les performances globales du pipeline RAG (Retrieval-Augmented Generation) de Tenglaafi, assistant médical spécialisé dans les maladies tropicales et les plantes médicinales.

Elle quantifie la cohérence entre les documents récupérés (R) et la réponse générée (G) à partir d'un jeu de 20 questions médicales de référence.

**Processus complet du pipeline évalué :**

```
collecte → embeddings → indexation → génération → évaluation
```

## 2. Configuration expérimentale

| Élément | Détail |
|---------|--------|
| Pipeline testé | src/rag_pipeline/rag.RAGPipeline |
| Base vectorielle | ChromaDB (collection tropical_medicine) |
| Modèle d'embeddings | sentence-transformers/paraphrase-multilingual-mpnet-base-v2 |
| Modèle LLM | mistralai/Mistral-7B-Instruct-v0.3 |
| Corpus indexé | data/corpus.json – 1 531 documents |
| Questions d'évaluation | evaluation/tests/evaluation_results/questions.json |
| Script d'évaluation | evaluation/evaluate.py |
| Fichiers résultats | evaluation/tests/evaluation_results/evaluation_results.json et .csv |
| Mode d'exécution | Indexation complète, puis force_reindex=False |

## 3. Structure des sorties

Deux formats complémentaires sont produits :

### a) evaluation_results.json

Contient, pour chaque question :
- la question, la réponse attendue et la réponse générée
- la liste des documents sources extraits
- l'ensemble des métriques calculées automatiquement

```json
{
  "id": 1,
  "question": "Quels sont les principaux symptômes du paludisme non compliqué ?",
  "metrics": {
    "retrieval_precision": 0.44,
    "answer_completeness": 0.47,
    "semantic_similarity": 0.60,
    "response_time": 2.38
  }
}
```

### b) evaluation_results.csv

Format tabulaire plat pour inspection manuelle, post-traitement ou intégration dans un tableur / dashboard.

## 4. Métriques utilisées

Les métriques proviennent du module evaluation/metrics.py.

| Métrique | Description | Interprétation |
|----------|-------------|----------------|
| Retrieval Precision | % de mots-clés attendus retrouvés dans les documents sélectionnés | Qualité du moteur de recherche vectoriel |
| Answer Completeness | Couverture des mots-clés attendus dans la réponse | Indique l'exhaustivité des réponses |
| Semantic Similarity | Similarité cosinus entre réponse générée et référence | Fidélité du contenu généré |
| Pertinence (/5) | Pondération combinée : 60 % similarité + 40 % complétude | Mesure globale de qualité perçue |
| Response Time (s) | Temps moyen d'exécution par requête | Indicateur de rapidité du pipeline |

## 5. Résultats globaux

D'après le résumé agrégé du JSON (summary) :

| Métrique | Score moyen |
|----------|-------------|
| Précision retrieval moyenne | 0.4483 |
| Précision retrieval (/5) | 2.2415 / 5 |
| Complétude réponse moyenne | 0.4558 |
| Similarité sémantique moyenne | 0.607 |
| Pertinence (/5) moyenne | 2.733 / 5 |
| Temps moyen de réponse | 2.386 s |
| Nombre de questions testées | 20 |

## 6. Analyse qualitative

### 6.1 Points forts

**Cohérence sémantique solide (≈ 0.61) :**
le modèle Mistral-7B reformule avec fidélité les notions médicales.

**Latence maîtrisée (~ 2.4 s) :**
performance remarquable pour un modèle de 7 B de paramètres.

**Résilience du retrieval (~ 45 %) :**
bon ciblage des documents malgré un corpus hétérogène.

### 6.2 Limites observées

**Complétude moyenne faible (~ 0.46) :**
certaines réponses restent superficielles (symptômes manquants, oublis contextuels).

**Présence de zéros artificiels :**
dus à des différences d'orthographe ou d'accents (p. ex. "fièvre" vs "fievre").

**Absence fréquente de citations explicites :**
le LLM n'inclut pas toujours [Document X] dans la réponse finale.

## 7. Interprétation des scores

| Intervalle | Interprétation |
|------------|----------------|
| > 0.7 | Excellente cohérence et précision |
| 0.5 – 0.7 | Bonne qualité, améliorable |
| 0.3 – 0.5 | Moyenne, couverture partielle |
| < 0.3 | Réponse faible ou hors-sujet |

Le score global (≈ 0.6) positionne Tenglaafi dans la zone de cohérence correcte : le système comprend la majorité des questions et fournit des réponses médicalement plausibles.

## 8. Analyse du corpus et du retrieval

Le corpus mixte (OMS, PubMed, PDF locaux) entraîne des réponses parfois trop générales.

Les documents longs ou peu structurés diluent la pertinence du retrieval.

Un affinage sémantique des embeddings (modèle biomédical FR) permettrait d'améliorer la précision et la couverture des réponses.

## 9. Perspectives d'amélioration

| Axe | Proposition |
|-----|-------------|
| Retrieval | Fine-tuning avec un modèle biomédical francophone (BioClinicalBERT, CamemBERT-Med). |
| Prétraitement | Nettoyer et segmenter les textes (phrases courtes, suppression des doublons). |
| LLM Prompting | Ajouter contraintes de style : « Cite au moins une source ». |
| Évaluation | Introduire un ratings.json humain pour calibrer la pertinence subjective. |
| Corpus | Séparer les sections "plantes" et "maladies" pour affiner le contexte. |
| Interface | Retour visuel des sources pour validation rapide côté utilisateur. |

## 10. Conclusion

Le pipeline RAG Tenglaafi atteint un bon équilibre entre rapidité, cohérence linguistique et compréhension médicale, malgré un corpus hétérogène.

Les prochains travaux viseront à :
- renforcer la pertinence des documents récupérés
- enrichir le contexte avant génération
- et améliorer la complétude des réponses via un prompting adaptatif

**En résumé :** Tenglaafi RAG est prêt pour un usage expérimental et éducatif, mais nécessitera un affinement du corpus et du LLM pour un usage clinique fiable.

## 11. Références des fichiers d'évaluation

| Fichier | Description | Emplacement |
|---------|-------------|-------------|
| evaluation/evaluate.py | Script principal d'évaluation | evaluation/ |
| evaluation/metrics.py | Calcul et normalisation des métriques | evaluation/ |
| evaluation/tests/evaluation_results/evaluation_results.json | Résultats détaillés question → réponse | evaluation/tests/evaluation_results/ |
| evaluation/tests/evaluation_results/evaluation_results.csv | Tableau plat pour inspection et scoring | evaluation/tests/evaluation_results/ |