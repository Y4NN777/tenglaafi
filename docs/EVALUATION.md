#  Évaluation du pipeline RAG du chatbot Tenglaafi

## 1. Objectif général

Cette phase vise à quantifier les performances globales du pipeline RAG (Retrieval-Augmented Generation) de Tenglaafi, à partir d'un jeu de 20 questions médicales portant sur les maladies tropicales et les plantes médicinales.
Elle évalue la cohérence entre les documents récupérés (R) et la réponse générée (G), en suivant le protocole de l'étape 5 du hackathon :

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
| Corpus indexé | data/corpus.json — 1531 documents |
| Questions d'évaluation | evaluation/tests/evaluation_results/questions.json |
| Script d'évaluation | evaluation/evaluate.py |
| Fichiers résultats | evaluation/tests/evaluation_results/evaluation_results.json & .csv |

L'évaluation s'est déroulée après indexation complète (make index), avec force_reindex=False pour utiliser la base persistée.

## 3. Structure des sorties

Le script génère deux fichiers complémentaires :

### evaluation_results.json

Contient pour chaque question :
- la question posée et la réponse attendue,
- la réponse générée par Tenglaafi,
- les documents sources récupérés,
- et les métriques calculées :

```json
{
  "id": 1,
  "question": "...",
  "metrics": {
    "retrieval_precision": 0.44,
    "answer_completeness": 0.47,
    "semantic_similarity": 0.60,
    "response_time": 2.38
  }
}
```

### evaluation_results.csv

Tableau plat reprenant ces informations pour inspection manuelle, calculs externes ou visualisations.

## 4. Métriques utilisées

Les métriques proviennent du module evaluation/metrics.py.

| Métrique | Description | Interprétation |
|----------|-------------|----------------|
| Retrieval Precision | % de mots-clés attendus présents dans les documents récupérés. | Capacité du moteur vectoriel à cibler les bons passages du corpus. |
| Answer Completeness | Taux de couverture des mots-clés attendus dans la réponse. | Indique si la réponse du LLM couvre tous les aspects essentiels. |
| Semantic Similarity | Cosine de similarité entre la réponse générée et la référence. | Mesure la cohérence sémantique globale du texte produit. |
| Response Time (s) | Temps d'exécution moyen par requête. | Indicateur de latence et d'efficacité du pipeline. |

## 5. Résultats globaux

Les résultats agrégés sont extraits du champ "summary" du JSON, calculé automatiquement par evaluate.py :

| Métrique | Score moyen |
|----------|-------------|
| 🔹 Précision retrieval moyenne | 0.4483 |
| 🔹 Complétude réponse moyenne | 0.4558 |
| 🔹 Similarité sémantique moyenne | 0.607 |
| 🔹 Temps moyen de réponse | 2.3862 s |
| 🔹 Nombre total de questions | 20 |

## 6. Analyse qualitative

###  6.1 Points forts

- **Cohérence sémantique élevée (0.607)** :
  le modèle Mistral-7B parvient à reformuler correctement les concepts médicaux du contexte.

- **Latence maîtrisée (~2.4 s)** sur CPU, remarquable pour un LLM de cette taille.

- **Robustesse du retrieval** : la précision avoisine 45%, ce qui est bon pour un corpus de plus de 1500 documents.

###  6.2 Points à améliorer

- **Complétude moyenne faible (~0.46)** : certaines réponses omettent des détails précis (symptômes secondaires, termes techniques).

- **Zéros fréquents pour retrieval_precision et answer_completeness** :
  ces cas proviennent souvent de variations lexicales (pluriels, accents, synonymes).
  → Un raffinage du prétraitement linguistique et des mots-clés réduira ces écarts.

- **Manque de citations directes** : bien que les sources soient intégrées dans le contexte, le LLM ne les mentionne pas toujours explicitement dans la réponse.

## 7. Interprétation

### 7.1 Lecture rapide des scores

| Plage | Interprétation |
|-------|----------------|
| > 0.7 | Excellente performance |
| 0.5 – 0.7 | Bonne cohérence mais améliorable |
| 0.3 – 0.5 | Moyenne, contextualisation partielle |
| < 0.3 | Faible ou hors-sujet |

Les résultats actuels positionnent Tenglaafi dans la plage intermédiaire supérieure (≈0.6) :
le système comprend globalement les questions et répond de façon plausible, mais l'extraction d'informations reste perfectible.

### 7.2 Impact du corpus

Les tests révèlent que la qualité des documents indexés influence directement la précision du retrieval.
Les textes très génériques (OMS, Wikipédia) réduisent la spécificité du vecteur.
Un filtrage thématique plus strict améliorerait la correspondance conceptuelle.

## 8. Perspectives d'amélioration

| Axe | Action recommandée |
|-----|-------------------|
| Retrieval | Affiner les embeddings avec un modèle biomédical francophone (BioClinicalBERT, CamemBERT-med). |
| Réindexation | Filtrer les doublons et les phrases génériques avant la vectorisation. |
| LLM | Ajouter un prompt contextuel plus directif (mention obligatoire des sources). |
| Métriques | Ajouter une pondération sur la longueur des réponses et la diversité des sources. |
| Évaluation | Introduire un ratings.json humain pour calibrer la pertinence perçue. |

## 9. Conclusion

Le pipeline RAG Tenglaafi démontre une performance solide pour une première version :
- bonne compréhension contextuelle,
- cohérence sémantique stable,
- latence maîtrisée.

Les marges de progression se situent surtout sur la précision du retrieval et la complétude des réponses, deux points directement améliorables par des raffinements de corpus et de prompt.

## 10. Références des fichiers

| Fichier | Rôle | Localisation |
|---------|------|--------------|
| evaluation/evaluate.py | Script principal d'évaluation | evaluation/ |
| evaluation/metrics.py | Calcul des métriques et normalisation linguistique | evaluation/ |
| evaluation/tests/evaluation_results/evaluation_results.json | Résultats complets question par question | evaluation/tests/evaluation_results/ |
| evaluation/tests/evaluation_results/evaluation_results.csv | Tableau plat pour export manuel ou Excel | evaluation/tests/evaluation_results/ |