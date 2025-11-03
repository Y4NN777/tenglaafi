"""
Module: data_loader

Overview:
    Le module `data_loader` regroupe les utilitaires bas niveau nécessaires à la collecte
    et au traitement de données textuelles dans le cadre du pipeline RAG.
    Il fournit des composants indépendants et réutilisables pour :
        - le scraping web et la validation de contenu textuel,
        - la recherche d’articles scientifiques via PubMed,
        - la segmentation de texte médical long en unités cohérentes,
        - le chargement de documents PDF médicaux locaux.

    Ce module constitue la base de la phase de collecte du système Tenglaafi.
    Il veille à ce que toutes les données utilisées soient propres, normalisées et
    prêtes à être vectorisées.

Rôle des @staticmethod:
    Les méthodes décorées avec `@staticmethod` :
        - n’ont pas besoin d’accéder à l’état interne de la classe (`self`),
        - servent à regrouper des fonctions utilitaires logiquement liées à la classe,
        - facilitent la réutilisation sans instancier l’objet (ex. WebScraper.clean_text("...")).
    Ce choix simplifie la conception et renforce la cohérence fonctionnelle :
    chaque méthode fait partie d’un groupe logique (par ex. nettoyage ou validation)
    sans dépendre d’un contexte d’instance.

Classes et Fonctions:
    1. class WebScraper
        - Fournit des outils pour extraire, nettoyer et valider du texte issu du web (HTML/PDF).
        - Méthodes:
            - clean_text(text: str) -> str
                Normalise et nettoie le texte brut.
            - validate_content(content: str, min_length: int = 100) -> bool
                Valide la qualité du contenu.
            - fetch_url(url: str, timeout: int = 15) -> Optional[dict]
                Télécharge et extrait le contenu d’une URL.

    2. class PubMedAPI
        - Client minimaliste pour l’API PubMed (E-utilities).
        - Méthodes:
            - search_articles(query: str, max_results: int = 50) -> List[str]
                Recherche des articles par mot-clé.
            - fetch_abstract(pmid: str) -> Optional[dict]
                Récupère le résumé d’un article PubMed.

    3. class MedicalTextSplitter
        - Diviseur de texte spécialisé pour les documents médicaux longs.
        - Méthodes:
            - __init__(chunk_size: int = 1000, chunk_overlap: int = 200)
                Initialise le séparateur de texte médical.
            - split_medical_text(text: str) -> List[str]
                Divise un texte en segments cohérents pour RAG.

    4. class PDFLoader
        - Chargeur de documents PDF médicaux locaux.
        - Méthodes:
            - load_pdf_from_directory(pdf_dir: str) -> List[dict]
                Charge et extrait le texte de tous les fichiers PDF d’un répertoire local.

Notes de Conception:
    - Chaque classe est indépendante et testable individuellement.
    - Le module respecte les principes de modularité et de traçabilité.
    - L’utilisation de @staticmethod maintient les classes stateless.
    - Tous les retours suivent un format typé et cohérent avec le reste du pipeline.
"""


# Librairies standard et tierces
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Optional, Dict
import logging
from pathlib import Path
import mimetypes

# Configuration du logging
from ..core import LOGGING_CONFIG
import logging.config

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)



class WebScraper:
    
    """
     Scraper web generique avec nettoyage et validation
    """
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
         Normalise et nettoie le texte

        Args:
            text (str): texte brute a nettoyer

        Returns:
            str: texte nettoyé
        """
        
        if not text:
            return ""
        
        # Supprimer les espaces inutiles
        text = re.sub(r'\s+', ' ', text)
        # Supprime caracteres speciaux problematiques
        text = re.sub(r'[^\w\s,.!?;:()\-]', '', text)
        # Normaliser les apostrophes 
        text = text.replace("'", "'")    
        
        return text.strip()


    @staticmethod
    def validate_content(content: str, min_length: int = 100) -> bool:
        
        """
         Valide le contenu en fonction de critères simples

        Args:
            content (str): contenu a valider
            min_length (int, optional): longueur minimale. Defaults to 100.

        Returns:
            bool: True si valide, False sinon
        """
        if not content or len(content) < min_length:
            return False
        
        # Verifier ratio lettres/caracteres
        alpha_ratio = sum(c.isalpha() for c in content) / len(content)
        return alpha_ratio >= 0.6
    
    @staticmethod
    def fetch_url(url: str, timeout: int = 15) -> Optional[str]:
        """
         Telecharge et extrait le contenu d'une URL ( HTML ou PDF)

        Args:
            url (str): URL à scraper
            timeout (int): delai d'attente en secondes. Defaults to 15.

        Returns:
            Dict :{title, text, url, length} ou None si echec
        """

        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Medical Research Bot)'}
            response = requests.get(url, timneout=timeout, headers=headers)
            response.raise_for_status()
            
            # Detecter le type de contenu
            content_type = response.headers.get('Content-Type', '')
            mime_type = mimetypes.guess_type(url)[0]
            
            # Si PDF retourner marqueur PDF
            
            if "pdf" in content_type or (mime_type and "pdf" in mime_type):
                return {
                    "title": Path(url).stem,
                    "text": f"PDF Document : {url}",
                    "length": 0,
                    "type": "pdf",
                }
            # Sinon parser HTML
            soup = BeautifulSoup(response.content, "html.parser")
            
            title_tag = soup.find("title") or soup.find("h1")
            title = title_tag.get_text(strip=True) if title_tag else "Sans Titre"
            
            content_tags = (
                soup.find_all("article") or
                soup.find_all("main") or
                soup.find_all("p")
            )
            
            paragraphs = []
            
            for tag in content_tags:
                text =  tag.get_text(separator =" ", strip=True)
                if len(text) > 50: # Filtrer courts paragraphes
                    paragraphs.append(text)
                    
            content = "".join(paragraphs)
            
            # Validation 
            
            if not WebScraper.validate_content(content):
                logging.warning(f"Contenu invalide pour l'URL: {url}")
                return None
            
            
            return {
                "title": WebScraper.clean_text(title),
                "text": WebScraper.clean_text(content),
                "url": url,
                "length": len(content),
                "type": "html",
            }
        except requests.exceptions.Timeout:
            logging.warning(f"Timeout lors du scraping de l'URL: {url}")
            return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Erreur  Reseau lors du téléchargement de l'URL: {url} - {e}")
            return None
        except Exception as e:
            logging.error(f"Erreur inattendue lors du scraping de l'URL: {url} - {e}")
            return None
    
    
class PubMedAPI:
    """
     Client pour l'APi PubMed (E-utils)
    """

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    @staticmethod
    def search_articles(query: str, max_results: int = 50) -> List[str]:
        
        """
         Recherche des articles PubMed par mot-clé

        Args:
            query (str): terme de recherche
            max_results (int): nombre maximum de résultats. Defaults to 10.

        Returns:
            List[str]: liste d'IDs d'articles PubMed
        """
        
        try:
            
            search_url = (
                f"{PubMedAPI.BASE_URL}esearch.fcgi?"
                f"db=pubmed&term={query}&retmax={max_results}&retmode=json"
            )
            
            response = requests.get(search_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            pmids = data.get("esearchresult", {}).get("idlist", [])
            
            logger.info(f"Pubmed query '{query}' : {len(pmids)} résultats.")
            return pmids

        except Exception as e:
            logging.error(f"Erreur lors de la recherche PubMed: {e}")
            return []
    
    
    @staticmethod
    def fetch_abstract(pmid: str) -> Optional[Dict]:
        """
         Récupère le résumé d'un article PubMed par son PMID

        Args:
            pmid (str): ID de l'article PubMed

        Returns:
            Dict {title, text, url} ou None
        """

        try:
            fetch_url = f"{PubMedAPI.BASE_URL}efetch.fcgi?db=pubmed&id={pmid}&retmode=xml"
            response = requests.get(fetch_url, timeout=10)
            response.raise_for_status()
            
            from xml.etree import ElementTree as ET
            # Parsing XML
            xml_content = ET.fromstring(response.content)

            if xml_content.find(".//Abstract") is None or xml_content.find(".//AbstractText") is None:
                logging.warning(f"Aucun résumé trouvé pour le PMID: {pmid}")
                return None
            
            return {
                "title": f"Pubmed_{pmid}",
                "text": xml_content.find(".//AbstractText").get_text(strip=True),
                "url": fetch_url or f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "length": len(xml_content.find(".//AbstractText").get_text(strip=True)),
            }
            
            
        except Exception as e:
            logging.error(f"Erreur lors de la récupération de l'abstract PubMed: {e}")
            return None

    
    
class MedicalTextSplitter:
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
         Initialise le diviseur de texte médical

        Args:
            chunk_size (int, optional): taille des morceaux. Defaults to 500.
            overlap (int, optional): chevauchement entre morceaux. Defaults to 50.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=[
                "\n\n",  # Paragraphs
                "\n",    # Lines  
                ". ",    # Sentences
                " ",     # Words
            ],
            length_function=len
        )
            
        except ImportError:
            raise ImportError("Veuillez installer langchain pour utiliser MedicalTextSplitter.")
        
    def split_medical_text(self, text: str) -> List[str]:
        """
         Divise le texte médical en morceaux gérables

        Args:
            text (str): texte médical à diviser

        Returns:
            List[str]: liste de morceaux de texte
        """
        return self.splitter.split_text(text)
    
    
class PDFLoader:
    """
     Chargeur PDF spécialisé pour documents médicaux locaux
    """
    
    @staticmethod
    def load_pdf_from_directory(pdf_dir: str) -> List[str]:
        """
         Charge tous les PDFs d'un répertoire local et extrait le texte

        Args:
            pdf_dir (str): chemin vers le répertoire contenant les fichiers PDF

        Returns:
            Liste de documents [{id, title, text, url, source}]
        """

        try:
            from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
            
            loader = DirectoryLoader(
                pdf_dir,
                glob="**/*.pdf",
                loader_cls=PyPDFLoader,
            )
            
            documents = loader.load()
            
            # Grouper les pages par PDFs
            
            pdf_groups = {} 
            for doc in documents:
                pdf_path = doc.metadata.get("source", "unknown.pdf")
                if pdf_path not in pdf_groups:
                    pdf_groups[pdf_path] = []
                pdf_groups[pdf_path].append(doc.page_content)
                
            # Appliquer le chunking 
            chunked_docs = []
            doc_id = 0
            
            for pdf_path, pages in pdf_groups.items():
                # Concatenate all pages from same PDF
                full_text = "\n\n".join(pages)
                
                # Split into chunks
                text_splitter = MedicalTextSplitter()
                chunks = text_splitter.split_medical_text(full_text)
                
                # Create documents from chunks
                for chunk in chunks:
                    chunked_docs.append({
                        "id": doc_id,
                        "title": f"{Path(pdf_path).stem} (chunk {doc_id})",
                        "text": WebScraper.clean_text(chunk),
                        "url":pdf_path,
                        "length": len(chunk),
                        "source": "PDF_chunked"
                    })
                    doc_id += 1
                    
            return chunked_docs
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors du chargement des PDFs depuis {pdf_dir}: {e}")
            return []
