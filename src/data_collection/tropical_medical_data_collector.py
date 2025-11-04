"""
src/data_collection/tropical_medical_data_collector.py
Orchestrateur de collecte pour données médicales tropicales

Utilise les utilitaires de data_utils pour la logique bas niveau.
Se concentre sur la stratégie de collecte et l'orchestration.
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
import logging
import time
import requests
from urllib.parse import urlparse

import os, sys
from pathlib import Path as _Path

# Trouver le root du projet en recherchant l'ancêtre nommé 'src'.
# Cela fonctionne que le module soit exécuté comme script ou importé.
_p = _Path(__file__).resolve()
project_root = None
for anc in _p.parents:
    if anc.name == "src":
        project_root = str(anc.parent)
        break
if project_root is None:
    # Fallback raisonnable (deux niveaux au-dessus)
    project_root = str(_p.parents[2]) if len(_p.parents) > 2 else str(_p.parent)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.config import LOGGING_CONFIG
import logging.config

# Import des utilitaires via le package `src`
from src.rag_pipeline.data_utils import WebScraper, PubMedAPI, PDFLoader

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


class TropicalMedicalDataCollector:
    """
    Orchestrateur de collecte de données médicales tropicales
    
    Responsabilités:
    - Définir les sources médicales pertinentes
    - Orchestrer la collecte depuis WHO, PubMed, Plants, PDFs
    - Construire un corpus unifié de 500+ documents
    - Sauvegarder le corpus et les métadonnées
    - Tracker les échecs et implémenter des stratégies de récupération
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
        "https://www.who.int/news-room/fact-sheets/detail/trypanosomiasis-human-african-(sleeping-sickness)",
        "https://www.who.int/health-topics/neglected-tropical-diseases",
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
        "https://www.paho.org/en/topics/neglected-tropical-and-vector-borne-diseases"
    ]

    PUBMED_QUERIES = [
        "tropical diseases treatment", "medicinal plants Africa", "herbal medicine tropical diseases",
        "malaria traditional medicine", "artemisia antimalarial", "neem medicinal properties",
        "neglected tropical diseases control", "vector borne diseases epidemiology",
        "traditional medicine tropical diseases Africa", "herbal remedies malaria treatment",
        "Zika virus epidemiology", "oral drug therapy neglected tropical diseases",
        "natural product tropical infectious diseases", "neglected tropical diseases mass drug administration",
        "integrated prevention treatment neglected tropical diseases",
        "burden neglected tropical diseases diagnosis access",
        "comprehensive review neglected tropical diseases", "drug development tropical diseases open source",
        "public health surveillance tropical diseases Madagascar", "health promotion neglected tropical diseases",
        "advances diagnosis treatment tropical infections", "herbal remedies tropical fever",
        "traditional anti-parasitic medicinal plants", "climate change impact tropical diseases",
        "vector control tropical disease prevention", "vaccine candidates tropical infectious diseases"
    ]

    MEDICINAL_PLANTS_URLS = [
        "https://journals.openedition.org/ethnoecologie/8925?lang=en",
        "https://pmc.ncbi.nlm.nih.gov/articles/PMC8199769/",
        "https://www.scribd.com/document/516515095/La-banque-de-donnees-ethnobotaniques-PHARMEL-sur-les-plantes-medicinales-africaines",
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
        "https://hsd-fmsb.org/index.php/hra/article/view/5940"
    ]
    
    # === CONFIGURATION AVANCEE ===
    
    # Domaines autorisés pour SSL non-vérifié (certificats expirés connus)
    SSL_WHITELIST = [
        "wahooas.org",
        "wahoas.org"
    ]
    
    # Domaines connus pour être des portails non-scrapables
    PORTAL_DOMAINS = [
        "africanplantdatabase.ch",
        "gbif.biodiversity.be",
        "plants.jstor.org"
    ]
    
    # Domaines nécessitant authentification
    AUTH_REQUIRED_DOMAINS = [
        "researchgate.net",
        "jstor.org"
    ]
    
    def __init__(self, output_dir: str = "data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.corpus = []
        self.scraper = WebScraper()
        self.pubmed = PubMedAPI()
        self.pdf_loader = PDFLoader()
        
        # Tracking des échecs
        self.failed_sources = {
            "WHO": [],
            "PubMed": [],
            "MedicinalPlants": [],
            "PDFs": []
        }
    
    # === METHODES UTILITAIRES AJOUTEES ===
    
    def _is_portal_url(self, url: str) -> bool:
        """
        Vérifie si une URL pointe vers un portail non-scrapable
        
        Args:
            url: URL à vérifier
            
        Returns:
            True si c'est un portail connu
        """
        domain = urlparse(url).netloc
        return any(portal in domain for portal in self.PORTAL_DOMAINS)
    
    def _requires_auth(self, url: str) -> bool:
        """
        Vérifie si une URL nécessite une authentification
        
        Args:
            url: URL à vérifier
            
        Returns:
            True si authentification requise
        """
        domain = urlparse(url).netloc
        return any(auth_domain in domain for auth_domain in self.AUTH_REQUIRED_DOMAINS)
    
    def _needs_ssl_bypass(self, url: str) -> bool:
        """
        Vérifie si une URL nécessite un bypass SSL
        
        Args:
            url: URL à vérifier
            
        Returns:
            True si le domaine est dans la whitelist SSL
        """
        domain = urlparse(url).netloc
        return any(whitelisted in domain for whitelisted in self.SSL_WHITELIST)
    
    def _convert_fr_to_en(self, url: str) -> str:
        """
        Convertit une URL WHO française en anglaise
        
        Args:
            url: URL originale avec /fr/
            
        Returns:
            URL avec /fr/ remplacé par /en/
        """
        return url.replace("/fr/news-room", "/news-room").replace("/fr/health-topics", "/health-topics")
    
    def _retry_with_backoff(self, func, max_retries: int = 3, initial_delay: float = 1.0):
        """
        Réessaie une fonction avec backoff exponentiel
        
        Args:
            func: Fonction à exécuter
            max_retries: Nombre maximum de tentatives
            initial_delay: Délai initial en secondes
            
        Returns:
            Résultat de la fonction ou None
        """
        delay = initial_delay
        for attempt in range(max_retries):
            try:
                result = func()
                if result:
                    return result
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.debug(f"Tentative {attempt + 1}/{max_retries} echouee, retry dans {delay}s: {e}")
                    time.sleep(delay)
                    delay *= 2  # Backoff exponentiel
                else:
                    logger.debug(f"Echec definitif apres {max_retries} tentatives")
                    raise
        return None
    
    def _track_failure(self, source_type: str, identifier: str, error_type: str, details: str = ""):
        """
        Enregistre un échec de collecte
        
        Args:
            source_type: Type de source (WHO, PubMed, etc.)
            identifier: URL ou PMID
            error_type: Type d'erreur (404, SSL_CERT_EXPIRED, etc.)
            details: Détails supplémentaires
        """
        failure_record = {
            "identifier": identifier,
            "error": error_type,
            "details": details,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.failed_sources[source_type].append(failure_record)
        logger.debug(f"Echec tracké - {source_type}: {identifier} ({error_type})")
    
    def _validate_pdf_directory(self, pdf_dir: str) -> bool:
        """
        Valide l'existence et le contenu du répertoire PDF
        
        Args:
            pdf_dir: Chemin du répertoire
            
        Returns:
            True si le répertoire existe et contient des PDFs
        """
        path = Path(pdf_dir)
        
        if not path.exists():
            logger.warning(f"Repertoire PDF inexistant: {pdf_dir}")
            self._track_failure("PDFs", pdf_dir, "DIR_NOT_FOUND", "Le repertoire n'existe pas")
            return False
        
        if not path.is_dir():
            logger.warning(f"Le chemin n'est pas un repertoire: {pdf_dir}")
            self._track_failure("PDFs", pdf_dir, "NOT_A_DIRECTORY", "Le chemin pointe vers un fichier")
            return False
        
        pdf_files = list(path.glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"Aucun fichier PDF trouve dans: {pdf_dir}")
            self._track_failure("PDFs", pdf_dir, "EMPTY_DIRECTORY", "Aucun fichier .pdf present")
            return False
        
        logger.info(f"Repertoire PDF valide: {len(pdf_files)} fichiers trouves")
        return True
    
    # === MÉTHODES DE COLLECTE PAR SOURCE (ENRICHIES) ===
    
    def collect_from_who(self) -> List[Dict]:
        """
        Collecte depuis WHO (Organisation Mondiale de la Santé)
        Avec fallback automatique FR -> EN pour les 404
        
        Returns:
            Liste de documents WHO
        """
        logger.info(" Phase 1/4: Collecte WHO Tropical Diseases")
        
        docs = []
        for idx, url in enumerate(self.WHO_URLS):
            try:
                # Tentative initiale
                doc = self.scraper.fetch_url(url)
                
                if doc:
                    doc["id"] = idx
                    doc["source"] = "WHO"
                    docs.append(doc)
                    logger.info(f"  WHO {idx+1}/{len(self.WHO_URLS)}")
                else:
                    # Si échec et URL française, tenter la version anglaise
                    if "/fr/" in url:
                        logger.debug(f"Tentative fallback EN pour: {url}")
                        en_url = self._convert_fr_to_en(url)
                        
                        try:
                            doc = self.scraper.fetch_url(en_url)
                            if doc:
                                doc["id"] = idx
                                doc["source"] = "WHO"
                                doc["url"] = en_url  # Mettre à jour l'URL utilisée
                                docs.append(doc)
                                logger.info(f"  WHO {idx+1}/{len(self.WHO_URLS)} (fallback EN)")
                            else:
                                self._track_failure("WHO", url, "HTTP_404", f"Echec aussi sur {en_url}")
                        except Exception as e:
                            self._track_failure("WHO", url, "FALLBACK_FAILED", str(e))
                    else:
                        self._track_failure("WHO", url, "FETCH_FAILED", "Reponse vide")
                
                time.sleep(1.0)  # Rate limiting
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    self._track_failure("WHO", url, "HTTP_404", "Page non trouvee")
                else:
                    self._track_failure("WHO", url, f"HTTP_{e.response.status_code}", str(e))
                logger.error(f"  Erreur WHO {url}: {e}")
            except Exception as e:
                self._track_failure("WHO", url, "UNKNOWN_ERROR", str(e))
                logger.error(f"  Erreur WHO {url}: {e}")
        
        logger.info(f"WHO: {len(docs)} documents collectes")
        return docs
    
    def collect_from_pubmed(self) -> List[Dict]:
        """
        Collecte depuis PubMed (articles scientifiques)
        Avec tracking des abstracts manquants
        
        Returns:
            Liste de documents PubMed
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
                    try:
                        abstract = self.pubmed.fetch_abstract(pmid)
                        
                        if abstract:
                            # Vérifier si l'abstract contient du texte
                            if abstract.get("text") and len(abstract.get("text", "").strip()) > 0:
                                abstract["id"] = doc_id
                                abstract["source"] = "PubMed"
                                abstract["has_abstract"] = True
                                docs.append(abstract)
                                doc_id += 1
                            else:
                                # Métadonnées présentes mais pas d'abstract
                                # Ce n'est pas un échec, on garde les métadonnées
                                abstract["id"] = doc_id
                                abstract["source"] = "PubMed"
                                abstract["has_abstract"] = False
                                abstract["text"] = ""  # Texte vide explicite
                                docs.append(abstract)
                                doc_id += 1
                                logger.debug(f"PMID {pmid}: metadonnees uniquement (pas d'abstract)")
                        else:
                            self._track_failure("PubMed", pmid, "FETCH_FAILED", "Reponse vide de l'API")
                    except Exception as e:
                        self._track_failure("PubMed", pmid, "FETCH_ERROR", str(e))
                        logger.debug(f"Erreur PMID {pmid}: {e}")
                
                time.sleep(1.0)  # Rate limiting
                
            except Exception as e:
                self._track_failure("PubMed", query, "QUERY_FAILED", str(e))
                logger.error(f"  Erreur PubMed query '{query}': {e}")
        
        logger.info(f"PubMed: {len(docs)} documents collectes")
        return docs
    
    def collect_from_medicinal_plants(self) -> List[Dict]:
        """
        Collecte depuis sources sur plantes médicinales tropicales
        Avec filtrage des portails, gestion SSL et authentification
        
        Returns:
            Liste de documents plantes médicinales
        """
        logger.info("\n Phase 3/4: Collecte Plantes Medicinales")
        
        docs = []
        doc_id = 3000  # Offset
        
        for idx, url in enumerate(self.MEDICINAL_PLANTS_URLS):
            # Vérifications préalables
            if self._is_portal_url(url):
                logger.info(f"   Plants {idx+1}/{len(self.MEDICINAL_PLANTS_URLS)} - SKIP (portail)")
                self._track_failure("MedicinalPlants", url, "PORTAL_SKIPPED", "URL identifiee comme portail non-scrapable")
                continue
            
            if self._requires_auth(url):
                logger.info(f"   Plants {idx+1}/{len(self.MEDICINAL_PLANTS_URLS)} - SKIP (auth requise)")
                self._track_failure("MedicinalPlants", url, "AUTH_REQUIRED", "Site necessite authentification")
                continue
            
            try:
                # Gestion SSL si nécessaire
                if self._needs_ssl_bypass(url):
                    logger.debug(f"Bypass SSL pour: {url}")
                    # Note: Nécessite modification de WebScraper pour accepter verify=False
                    # Pour l'instant on tente quand même
                
                # Tentative avec retry
                def fetch_attempt():
                    return self.scraper.fetch_url(url)
                
                doc = self._retry_with_backoff(fetch_attempt, max_retries=2)
                
                if doc:
                    doc["id"] = doc_id
                    doc["source"] = "MedicinalPlants"
                    docs.append(doc)
                    logger.info(f"   Plants {idx+1}/{len(self.MEDICINAL_PLANTS_URLS)}")
                    doc_id += 1
                else:
                    self._track_failure("MedicinalPlants", url, "FETCH_FAILED", "Reponse vide apres retries")
                
                time.sleep(1.5)  # Rate limiting plus prudent
                
            except requests.exceptions.SSLError as e:
                self._track_failure("MedicinalPlants", url, "SSL_CERT_EXPIRED", str(e))
                logger.error(f"   Erreur SSL Plants {url}: {e}")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    self._track_failure("MedicinalPlants", url, "HTTP_403", "Acces interdit")
                else:
                    self._track_failure("MedicinalPlants", url, f"HTTP_{e.response.status_code}", str(e))
                logger.error(f"   Erreur HTTP Plants {url}: {e}")
            except requests.exceptions.ConnectionError as e:
                self._track_failure("MedicinalPlants", url, "DNS_FAIL", str(e))
                logger.error(f"   Erreur DNS Plants {url}: {e}")
            except Exception as e:
                self._track_failure("MedicinalPlants", url, "UNKNOWN_ERROR", str(e))
                logger.error(f"   Erreur Plants {url}: {e}")
        
        logger.info(f"Plantes Medicinales: {len(docs)} documents collectes")
        return docs
    
    def collect_from_pdfs(self, pdf_dir: str = "data/raw") -> List[Dict]:
        """
        Charge les PDFs locaux
        Avec validation préalable du répertoire
        
        Args:
            pdf_dir: Répertoire contenant les PDFs
            
        Returns:
            Liste de documents PDF
        """
        logger.info("\n Phase 4/4: Chargement PDFs Locaux")
        
        # Validation du répertoire
        if not self._validate_pdf_directory(pdf_dir):
            logger.warning(f"Validation echouee pour: {pdf_dir}")
            return []
        
        try:
            docs = self.pdf_loader.load_pdfs_from_directory(pdf_dir)
            
            # Réassigner IDs avec offset
            for idx, doc in enumerate(docs):
                doc["id"] = 4000 + idx
            
            logger.info(f" PDFs Locaux: {len(docs)} documents charges")
            return docs
            
        except Exception as e:
            self._track_failure("PDFs", pdf_dir, "LOAD_ERROR", str(e))
            logger.error(f"Erreur lors du chargement des PDFs: {e}")
            return []
    
    # === ORCHESTRATION PRINCIPALE ===
    
    def generate_corpus(self, min_docs: int = 500) -> None:
        """
        Pipeline complet de collecte
        
        Orchestre toutes les sources et construit le corpus final
        
        Args:
            min_docs: Nombre minimum de documents requis
        """
        logger.info("=" * 70)
        logger.info("  DEBUT DE LA COLLECTE COMPLETE")
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
        logger.info(f"  RESULTATS FINAUX")
        logger.info("=" * 70)
        logger.info(f"  WHO: {len(who_docs)} docs")
        logger.info(f"  PubMed: {len(pubmed_docs)} docs")
        logger.info(f"  Plantes: {len(plant_docs)} docs")
        logger.info(f"  PDFs: {len(pdf_docs)} docs")
        logger.info(f"  TOTAL: {total} documents")
        
        # Statistiques d'échecs
        total_failures = sum(len(failures) for failures in self.failed_sources.values())
        if total_failures > 0:
            logger.info(f"  ECHECS: {total_failures} sources")
            for source_type, failures in self.failed_sources.items():
                if failures:
                    logger.info(f"    - {source_type}: {len(failures)} echecs")
        
        if total < min_docs:
            logger.warning(f"  Objectif non atteint: {total}/{min_docs}")
        else:
            logger.info(f"  Objectif atteint: {total}/{min_docs}")
        
        # Sauvegarde
        self.save_corpus()
        self.save_failed_sources()
    
    def save_corpus(self):
        """Sauvegarde le corpus et les métadonnées"""
        corpus_path = self.output_dir / "corpus.json"
        sources_path = self.output_dir / "sources.txt"
        
        # Corpus JSON
        with open(corpus_path, "w", encoding="utf-8") as f:
            json.dump(self.corpus, f, ensure_ascii=False, indent=2)
        
        # Sources TXT avec groupement par type
        with open(sources_path, "w", encoding="utf-8") as f:
            f.write("# Sources Medicales Tropicales\n\n")
            
            sources_by_type = {}
            for doc in self.corpus:
                src_type = doc.get("source", "Unknown")
                sources_by_type.setdefault(src_type, []).append(doc)
            
            for src_type, docs in sources_by_type.items():
                f.write(f"\n## {src_type} ({len(docs)} documents)\n")
                for doc in docs:
                    f.write(f"{doc['id']}\t{doc['title']}\t{doc.get('url', 'N/A')}\n")
        
        logger.info(f"\n Corpus sauvegarde: {corpus_path}")
        logger.info(f" Sources sauvegardees: {sources_path}")
    
    def save_failed_sources(self):
        """Sauvegarde le tracking des échecs"""
        failed_path = self.output_dir / "sources_failed.json"
        
        # Filtrer les sources sans échecs
        non_empty_failures = {
            source_type: failures 
            for source_type, failures in self.failed_sources.items() 
            if failures
        }
        
        if non_empty_failures:
            with open(failed_path, "w", encoding="utf-8") as f:
                json.dump(non_empty_failures, f, ensure_ascii=False, indent=2)
            
            logger.info(f" Echecs sauvegardes: {failed_path}")
            
            # Résumé des échecs par type d'erreur
            error_summary = {}
            for source_type, failures in non_empty_failures.items():
                for failure in failures:
                    error_type = failure["error"]
                    error_summary[error_type] = error_summary.get(error_type, 0) + 1
            
            logger.info("\n Resume des types d'erreurs:")
            for error_type, count in sorted(error_summary.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"   - {error_type}: {count}")
        else:
            logger.info(" Aucun echec a sauvegarder")


# === POINT D'ENTRÉE ===

if __name__ == "__main__":
    collector = TropicalMedicalDataCollector(output_dir="data")
    collector.generate_corpus(min_docs=500)
    
    # Statistiques finales
    stats = {
        "total": len(collector.corpus),
        "avg_length": sum(d.get("length", 0) for d in collector.corpus) / len(collector.corpus or [1]),
        "by_source": {}
    }
    
    for doc in collector.corpus:
        src = doc.get("source", "Unknown")
        stats["by_source"][src] = stats["by_source"].get(src, 0) + 1
    
    print("\n  Statistiques Finales:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))