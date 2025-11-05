"""tropical_medical_data_collector

Module de collecte de documents médicaux tropicaux.

Ce module fournit la classe `TropicalMedicalDataCollector` qui orchestre la
collecte de documents depuis plusieurs sources (WHO, PubMed, bases de plantes
médicinales et PDFs locaux), normalise les documents en un format commun et
produit des artefacts persistants (`data/corpus.json`, `data/sources.txt`).

Docstrings détaillées sont fournies pour la classe et les méthodes publiques
afin de faciliter la contribution et les tests.
"""

import json
from pathlib import Path
from typing import List, Dict
import logging
import time

from ..core.config import LOGGING_CONFIG
import logging.config

# Import des utilitaires
from ..rag_pipeline.data_utils import WebScraper, PubMedAPI, PDFLoader

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


class TropicalMedicalDataCollector:
    """Orchestrateur de collecte de documents médicaux tropicaux.

    Cette classe regroupe et normalise des documents provenant de plusieurs
    sources hétérogènes pour constituer un corpus exploitable par le pipeline
    RAG.

    Contract:
    - Input: paramètres de configuration (répertoires de sortie, URLs, etc.)
    - Output: fichiers persistés (``data/corpus.json``, ``data/sources.txt``)

    Attributs importants
    ---------------------
    output_dir : Path
        Répertoire où seront écrits les fichiers de sortie.
    corpus : list
        Liste accumulée des documents collectés (chaque document est un dict
        normalisé avec au minimum les clés: ``id``, ``title``, ``content``,
        ``source``).
    scraper : WebScraper
        Utilitaire pour télécharger et parser des pages web (WHO, plantes,...)
    pubmed : PubMedAPI
        Client pour interroger l'API PubMed.
    pdf_loader : PDFLoader
        Utilitaire pour extraire du texte depuis des fichiers PDF.

    Exceptions et erreurs
    ---------------------
    Les erreurs réseau et d'extraction sont loggées mais n'interrompent pas
    l'exécution globale : la collecte est tolérante et renvoie un corpus
    partiel en cas d'échecs ponctuels.

    Exemple
    -------
    >>> from src.data_collection.tropical_medical_data_collector import TropicalMedicalDataCollector
    >>> c = TropicalMedicalDataCollector(output_dir="data")
    >>> c.generate_corpus(min_docs=500)
    """

    # === CONFIGURATION DES SOURCES ===

    WHO_URLS = [
        "https://www.who.int/fr/news-room/fact-sheets/detail/malaria",
        "https://www.who.int/fr/news-room/fact-sheets/detail/dengue-and-severe-dengue",
        "https://www.who.int/fr/news-room/fact-sheets/detail/yellow-fever",
        "https://www.who.int/fr/news-room/fact-sheets/detail/leishmaniasis",
        "https://www.who.int/fr/news-room/fact-sheets/detail/schistosomiasis",
        "https://www.who.int/fr/news-room/fact-sheets/detail/lymphatic-filariasis",
        "https://www.who.int/fr/news-room/fact-sheets/detail/onchocerciasis",
        "https://www.who.int/fr/news-room/fact-sheets/detail/soil-transmitted-helminth-infections",
        "https://www.who.int/fr/news-room/fact-sheets/detail/chagas-disease-(american-trypanosomiasis)",
        "https://www.who.int/fr/news-room/fact-sheets/detail/african-trypanosomiasis",
        "https://www.who.int/fr/health-topics/neglected-tropical-diseases",
        "https://www.who.int/fr/news-room/fact-sheets",
        "https://www.paho.org/en/fact-sheets",
        "https://www.who.int/news-room/fact-sheets/detail/vector-borne-diseases",
        "https://www.who.int/fr/news-room/fact-sheets/detail/rabies",
        "https://www.who.int/fr/news-room/fact-sheets/detail/dracunculiasis-(guinea-worm-disease)",
        "https://www.who.int/fr/news-room/fact-sheets/detail/leprosy",
        "https://www.who.int/fr/news-room/fact-sheets/detail/trachoma",
        "https://www.who.int/fr/news-room/fact-sheets/detail/mycetoma",
        "https://www.who.int/fr/news-room/fact-sheets/detail/yaws",
        "https://www.who.int/fr/news-room/fact-sheets/detail/echinococcosis",
        "https://www.who.int/fr/news-room/fact-sheets/detail/foodborne-trematodiases",
        "https://www.who.int/fr/news-room/fact-sheets/detail/cryptosporidiosis",
        "https://www.who.int/fr/news-room/fact-sheets/detail/blindness-and-vision-loss",
        "https://www.paho.org/en/topics/neglected-tropical-and-vector-borne-diseases",
    ]

    PUBMED_QUERIES = [
        "tropical diseases treatment",
        "medicinal plants Africa",
        "herbal medicine tropical diseases",
        "malaria traditional medicine",
        "artemisia antimalarial",
        "neem medicinal properties",
        "neglected tropical diseases control",
        "vector borne diseases epidemiology",
        "traditional medicine tropical diseases Africa",
        "herbal remedies malaria treatment",
        "Zika virus epidemiology",
        "oral drug therapy neglected tropical diseases",
        "natural product tropical infectious diseases",
        "neglected tropical diseases mass drug administration",
        "integrated prevention treatment neglected tropical diseases",
        "burden neglected tropical diseases diagnosis access",
        "comprehensive review neglected tropical diseases",
        "drug development tropical diseases open source",
        "public health surveillance tropical diseases Madagascar",
        "health promotion neglected tropical diseases",
        "advances diagnosis treatment tropical infections",
        "herbal remedies tropical fever",
        "traditional anti-parasitic medicinal plants",
        "climate change impact tropical diseases",
        "vector control tropical disease prevention",
        "vaccine candidates tropical infectious diseases",
    ]

    MEDICINAL_PLANTS_URLS = [
        "https://journals.openedition.org/ethnoecologie/8925?lang=en",
        "https://pmc.ncbi.nlm.nih.gov/articles/PMC8199769/",
        "https://www.scribd.com/document/516515095/La-banque-de-donnees-ethnobotaniques-PHARMEL-sur-les-plantes-medicinales-africaines",
        "https://www.wahooas.org/web-ooas/sites/default/files/publications/2318/pharmacopee-de-lafrique-de-louest-french.pdf",
        "https://www.ebsco.com/research-starters/health-and-medicine/traditional-african-medicine",
        "https://africanplantdatabase.ch/",
        "https://gbif.biodiversity.be/nl/dataset/49c5b4ac-e3bf-401b-94b1-c94a2ad5c8d6",
        "https://plantuse.plantnet.org/fr/PROTA,_Introduction_aux_Plantes_m%C3%A9dicinales",
        "https://www.ethnopharmacologia.org/bibliotheque-ethnopharmacologie/pharmacopee-africaine/",
        "https://plants.jstor.org/collection/MEDPL",
        "https://library.au.int/traditional-medicine",
        "https://archives.au.int/handle/123456789/1846?show=full",
        "https://www.fao.org/4/w7261e/w7261e.pdf",
        "https://www.fao.org/4/y4496e/Y4496E42.htm",
        "https://www.researchgate.net/publication/313417728_Phytochimiques_des_plantes_medicinales_utilisees_dans_la_prise_en_charge_des_maladies_infantiles_au_SudBenin",
        "https://www.echocommunity.org/fr/resources/f4cbe972-a04a-4bb7-9c14-641b823b5fe8",
        "https://hsd-fmsb.org/index.php/hra/article/view/5940",
    ]

    def __init__(self, output_dir: str = "data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.corpus = []
        self.scraper = WebScraper()
        self.pubmed = PubMedAPI()
        self.pdf_loader = PDFLoader()

    # === MÉTHODES DE COLLECTE PAR SOURCE ===

    def collect_from_who(self) -> List[Dict]:
        """Collecte et normalise les pages WHO listées dans ``WHO_URLS``.

        Pour chaque URL, la méthode tente de récupérer le contenu via
        ``self.scraper.fetch_url`` puis d'ajouter les métadonnées minimales.

        Returns
        -------
        List[Dict]
            Liste de documents normalisés collectés depuis WHO. Chaque dictionnaire
            contient au minimum les clés: ``id``, ``title``, ``content``, ``source``.

        Notes
        -----
        - Les erreurs réseau sont interceptées et loggées. La méthode continue
          la collecte sur les URLs suivantes.
        - Un léger délai est appliqué entre requêtes pour respecter les
          limitations de taux.
        """
        logger.info(" Phase 1/4: Collecte WHO Tropical Diseases")

        docs = []
        for idx, url in enumerate(self.WHO_URLS):
            try:
                doc = self.scraper.fetch_url(url)

                if doc:
                    doc["id"] = idx
                    doc["source"] = "WHO"
                    docs.append(doc)
                    logger.info(f"  ✓ WHO {idx+1}/{len(self.WHO_URLS)}")

                time.sleep(1.0)  # Rate limiting

            except Exception as e:
                logger.error(f"  ✗ Erreur WHO {url}: {e}")

        logger.info(f"→ WHO: {len(docs)} documents collectés")
        return docs

    def collect_from_pubmed(self) -> List[Dict]:
        """Interroge PubMed pour une série de requêtes et récupère des abstracts.

        Le client ``self.pubmed`` est utilisé pour effectuer la recherche de
        PMIDs et la récupération des abstracts. Par souci de rapidité et de
        contrôle de quota, la méthode limite le nombre de résultats par requête.

        Returns
        -------
        List[Dict]
            Liste d'objets représentant les abstracts récupérés. Les clés
            attendues incluent : ``id``, ``title``, ``content`` (abstract),
            ``source``.

        Raises
        ------
        Exception
            Les erreurs de réseau sont capturées et loggées; la méthode ne
            propage pas les exceptions vers l'appelant.
        """
        logger.info("\n  Phase 2/4: Collecte PubMed Articles")

        docs = []
        doc_id = 1000  # Offset pour éviter collisions

        for query in self.PUBMED_QUERIES:
            try:
                # Recherche PMIDs
                pmids = self.pubmed.search_articles(query, max_results=50)

                # Récupération abstracts (limiter à 10 par query)
                for pmid in pmids[:10]:
                    abstract = self.pubmed.fetch_abstract(pmid)

                    if abstract:
                        abstract["id"] = doc_id
                        abstract["source"] = "PubMed"
                        docs.append(abstract)
                        doc_id += 1

                time.sleep(1.0)  # Rate limiting

            except Exception as e:
                logger.error(f"  ✗ Erreur PubMed query '{query}': {e}")

        logger.info(f"→ PubMed: {len(docs)} documents collectés")
        return docs

    def collect_from_medicinal_plants(self) -> List[Dict]:
        """Récupère des documents relatifs aux plantes médicinales à partir
        de la liste ``MEDICINAL_PLANTS_URLS``.

        Returns
        -------
        List[Dict]
            Documents normalisés extraits des pages ou PDFs listés.

        Notes
        -----
        - Certaines URLs peuvent pointer vers des PDFs (extraction via
          ``self.pdf_loader`` par le scraper) ou vers des pages HTML.
        - La méthode applique un délai de tempo plus long pour réduire la
          charge sur les serveurs externes.
        """
        logger.info("\n Phase 3/4: Collecte Plantes Médicinales")

        docs = []
        doc_id = 3000  # Offset

        for idx, url in enumerate(self.MEDICINAL_PLANTS_URLS):
            try:
                doc = self.scraper.fetch_url(url)

                if doc:
                    doc["id"] = doc_id
                    doc["source"] = "MedicinalPlants"
                    docs.append(doc)
                    logger.info(f"   Plants {idx+1}/{len(self.MEDICINAL_PLANTS_URLS)}")
                    doc_id += 1

                time.sleep(1.5)  # Rate limiting plus prudent

            except Exception as e:
                logger.error(f"   Erreur Plants {url}: {e}")

        logger.info(f"→ Plantes Médicinales: {len(docs)} documents collectés")
        return docs

    def collect_from_pdfs(self, pdf_dir: str = "data/raw") -> List[Dict]:
        """Charge et extrait le texte des fichiers PDF présents dans ``pdf_dir``.

        Parameters
        ----------
        pdf_dir : str
            Chemin vers le dossier contenant les fichiers PDF (relatif ou
            absolu). Par défaut ``data/raw``.

        Returns
        -------
        List[Dict]
            Liste des documents extraits depuis les PDFs. Chaque élément contient
            au minimum ``id``, ``title``, ``content`` et ``source``.

        Raises
        ------
        FileNotFoundError
            Si le répertoire n'existe pas. La méthode logge l'erreur et renvoie
            une liste vide au lieu de lever l'exception vers l'appelant.

        Notes
        -----
        - La méthode utilise ``self.pdf_loader.load_pdfs_from_directory`` pour
          l'extraction; selon la taille des PDFs, l'opération peut être longue.
        - Les IDs sont réassignés avec un offset pour éviter les collisions
          avec d'autres sources.
        """
        logger.info("\n Phase 4/4: Chargement PDFs Locaux")
        # Convertir en chemin absolu
        pdf_dir_path = Path(pdf_dir).resolve()
        logger.info(f" Chemin PDFs: {pdf_dir_path}")
        if not pdf_dir_path.exists():
            logger.error(f" ✗ Répertoire PDFs introuvable: {pdf_dir_path}")
            return []

        # Lister les PDFs trouvés
        pdf_files = list(pdf_dir_path.glob("*.pdf"))
        logger.info(f" PDFs trouvés: {len(pdf_files)}")
        for pdf in pdf_files:
            logger.info(f"   - {pdf.name}")

        docs = self.pdf_loader.load_pdfs_from_directory(str(pdf_dir_path))

        # Réassigner IDs avec offset
        for idx, doc in enumerate(docs):
            doc["id"] = 4000 + idx

        logger.info(f" PDFs Locaux: {len(docs)} documents chargés")
        return docs

    # === ORCHESTRATION PRINCIPALE ===

    def generate_corpus(self, min_docs: int = 500) -> None:
        """Orchestre la collecte complète depuis toutes les sources et sauvegarde
        le corpus.

        Parameters
        ----------
        min_docs : int
            Nombre minimum de documents visé (utilisé pour logging et alertes).

        Side effects
        ------------
        - Modifie l'attribut ``self.corpus`` en y ajoutant tous les documents
          collectés.
        - Écrit les fichiers ``corpus.json`` et ``sources.txt`` dans
          ``self.output_dir`` via ``self.save_corpus()``.

        Notes
        -----
        - La méthode est tolérante aux erreurs : si une source échoue, les
          autres sources continuent d'être traitées.
        """
        logger.info("=" * 70)
        logger.info("  DÉBUT DE LA COLLECTE COMPLÈTE")
        logger.info("=" * 70)

        # Phase 1: WHO
        who_docs = self.collect_from_who()
        self.corpus.extend(who_docs)

        # Phase 2: PubMed
        pubmed_docs = self.collect_from_pubmed()
        self.corpus.extend(pubmed_docs)

        # Phase 3: Plantes médicinales
        plant_docs = self.collect_from_medicinal_plants()
        self.corpus.extend(plant_docs)

        # Phase 4: PDFs locaux
        pdf_docs = self.collect_from_pdfs()
        self.corpus.extend(pdf_docs)

        # Validation
        total = len(self.corpus)
        logger.info("\n" + "=" * 70)
        logger.info(f"  RÉSULTATS FINAUX")
        logger.info("=" * 70)
        logger.info(f"  WHO: {len(who_docs)} docs")
        logger.info(f"  PubMed: {len(pubmed_docs)} docs")
        logger.info(f"  Plantes: {len(plant_docs)} docs")
        logger.info(f"  PDFs: {len(pdf_docs)} docs")
        logger.info(f"  TOTAL: {total} documents")

        if total < min_docs:
            logger.warning(f"  Objectif non atteint: {total}/{min_docs}")
        else:
            logger.info(f"  Objectif atteint: {total}/{min_docs}")

        # Sauvegarde
        self.save_corpus()

    def save_corpus(self):
        """Persiste le corpus en JSON et écrit un fichier texte listant les
        sources regroupées par type.

        Le fichier JSON est encodé en UTF-8 et n'échoue pas sur des caractères
        non-ASCII grâce à ``ensure_ascii=False``. Le fichier texte contient une
        ligne par document au format: ``id\ttitle\turl``.
        """
        corpus_path = self.output_dir / "corpus.json"
        sources_path = self.output_dir / "sources.txt"

        # Corpus JSON
        with open(corpus_path, "w", encoding="utf-8") as f:
            json.dump(self.corpus, f, ensure_ascii=False, indent=2)

        # Sources TXT avec groupement par type
        with open(sources_path, "w", encoding="utf-8") as f:
            f.write("# Sources Médicales Tropicales\n\n")

            sources_by_type = {}
            for doc in self.corpus:
                src_type = doc.get("source", "Unknown")
                sources_by_type.setdefault(src_type, []).append(doc)

            for src_type, docs in sources_by_type.items():
                f.write(f"\n## {src_type} ({len(docs)} documents)\n")
                for doc in docs:
                    f.write(f"{doc['id']}\t{doc['title']}\t{doc.get('url', 'N/A')}\n")

        logger.info(f"\n Corpus sauvegardé: {corpus_path}")
        logger.info(f" Sources sauvegardées: {sources_path}")


# === POINT D'ENTRÉE ===

if __name__ == "__main__":
    collector = TropicalMedicalDataCollector(output_dir="data")
    collector.generate_corpus(min_docs=500)

    # Statistiques finales
    stats = {
        "total": len(collector.corpus),
        "avg_length": sum(d.get("length", 0) for d in collector.corpus)
        / len(collector.corpus or [1]),
        "by_source": {},
    }

    for doc in collector.corpus:
        src = doc.get("source", "Unknown")
        stats["by_source"][src] = stats["by_source"].get(src, 0) + 1

    print("\n  Statistiques Finales:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))
