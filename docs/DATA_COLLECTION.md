# Collecte de Données Médicales Tropicales

## Vue d'ensemble

Le module de collecte de données est responsable de la constitution d'un corpus de documents médicaux tropicaux à partir de diverses sources fiables. L'objectif est de construire une base de connaissances riche pour le système RAG (Retrieval-Augmented Generation).

## Sources de Données

### 1. Organisation Mondiale de la Santé (WHO)
- Fiches d'information sur les maladies tropicales
- Documentation sur les maladies tropicales négligées
- Directives et recommandations officielles

### 2. PubMed
- Articles scientifiques sur les maladies tropicales
- Recherches sur les traitements traditionnels et modernes
- Études épidémiologiques

### 3. Base de Données sur les Plantes Médicinales
- Documentation sur la médecine traditionnelle africaine
- Ressources ethnobotaniques
- Études sur les propriétés médicinales des plantes

### 4. Documents PDF Locaux
- Rapports techniques
- Publications académiques
- Documents de référence

## Utilisation

```python
from src.data_collection.tropical_medical_data_collector import TropicalMedicalDataCollector

# Initialisation du collecteur
collector = TropicalMedicalDataCollector(output_dir="data")

# Génération du corpus complet
collector.generate_corpus(min_docs=500)
```

## Structure des Données

Les documents collectés sont structurés comme suit :

```json
{
    "id": "identifiant_unique",
    "title": "Titre du document",
    "content": "Contenu textuel",
    "source": "WHO/PubMed/MedicinalPlants/PDF",
    "url": "URL source (si applicable)",
    "metadata": {
        "date": "Date de publication",
        "author": "Auteur(s)",
        "keywords": ["mot-clé1", "mot-clé2"]
    }
}
```

## Contrôle de Qualité

- Rate limiting intégré pour respecter les API
- Validation des sources et de l'intégrité des données
- Filtrage du contenu non pertinent
- Objectif minimum de 500 documents
- Sauvegarde des métadonnées pour traçabilité

## Sorties

Le collecteur génère deux fichiers principaux :
- `data/corpus.json` : Corpus complet au format JSON
- `data/sources.txt` : Liste détaillée des sources par type

## Maintenance

### Ajout de Nouvelles Sources

Pour ajouter une nouvelle source de données :

1. Définir les URLs ou paramètres de recherche
2. Implémenter une méthode de collecte spécifique
3. Intégrer la source dans la méthode `generate_corpus()`
4. Mettre à jour la documentation

### Limitations Connues

- Dépendance aux APIs externes
- Temps de collecte variable selon la disponibilité des sources
- Besoin de maintenance régulière des URLs