"""
Module: data_utils

Overview:
    Le module `data_utils` regroupe l’ensemble des utilitaires fondamentaux dédiés
    à la collecte, au nettoyage et à la préparation des données textuelles pour
    le pipeline RAG médical de Tenglaafi. Il agit comme couche de support entre
    la phase de collecte et la vectorisation des documents.

    Ce module fournit des composants indépendants et réutilisables permettant de :
        - Scraper et valider des contenus web textuels (HTML/PDF),
        - Interroger et extraire des résumés d’articles scientifiques via l’API PubMed,
        - Segmenter efficacement de longs textes médicaux,
        - Charger et découper des documents PDF en segments cohérents pour RAG.

    Il garantit que toutes les données utilisées soient propres, normalisées,
    et prêtes à être indexées dans la base vectorielle. Chaque classe est conçue
    pour être stateless et testable individuellement.

Rôle des @staticmethod:
    Les méthodes décorées avec `@staticmethod` :
        - Ne nécessitent pas d’accès à l’état interne de la classe (`self`),
        - Permettent le regroupement logique de fonctions utilitaires,
        - Favorisent la réutilisation sans instanciation (ex. `WebScraper.clean_text('...')`).
    Ce design renforce la modularité et la cohérence fonctionnelle, tout en
    simplifiant les tests unitaires et l’intégration.

Classes et Fonctions:
    1. class WebScraper
        - Fournit des outils pour extraire, nettoyer et valider le texte issu du web.
        - Méthodes:
            - clean_text(text: str) -> str
                Normalise et nettoie le texte brut (Unicode, apostrophes, ponctuation).
            - validate_content(content: str, min_length: int = 100) -> bool
                Vérifie la validité et la densité linguistique du contenu.
            - fetch_url(url: str, timeout: int = 15) -> Optional[dict]
                Télécharge et extrait le contenu d’une page HTML ou PDF.

    2. class PubMedAPI
        - Client minimaliste pour l’API PubMed (E-utilities).
        - Méthodes:
            - search_articles(query: str, max_results: int = 50) -> List[str]
                Recherche les identifiants d’articles à partir d’un mot-clé.
            - fetch_abstract(pmid: str) -> Optional[dict]
                Récupère et parse le résumé XML d’un article PubMed.

    3. class MedicalTextSplitter
        - Séparateur de texte médical optimisé pour le traitement RAG.
        - Méthodes:
            - __init__(chunk_size: int = 1000, chunk_overlap: int = 200)
                Initialise le découpeur de texte.
            - split_medical_text(text: str) -> List[str]
                Divise un texte en segments équilibrés et contextuellement cohérents.

    4. class PDFLoader
        - Charge et segmente des documents PDF médicaux locaux.
        - Méthodes:
            - load_pdfs_from_directory(pdf_dir: str) -> List[dict]
                Charge tous les fichiers PDF d’un répertoire et les découpe en chunks prêts à indexer.

Notes de Conception:
    - Toutes les classes sont indépendantes et testables individuellement.
    - L’import des dépendances critiques (LangChain loaders) est isolé et exposé au module
      pour faciliter les tests (mock/monkeypatch).
    - L’usage de `langchain-text-splitters` est privilégié pour assurer la compatibilité open-source.
    - Les sorties sont typées et structurées pour une intégration directe avec le pipeline RAG Tenglaafi.

Auteur : Y4NN777

"""


from __future__ import annotations

import logging
import logging.config
import mimetypes
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from ..core.config import LOGGING_CONFIG

# Configure logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Essaye d'importer les loaders LangChain une seule fois et expose au module (pour monkeypatch en tests)
try:  # pragma: no cover - import guard
    from langchain_community.document_loaders import (
        PyPDFLoader as _PyPDFLoader,
        DirectoryLoader as _DirectoryLoader,
    )
except Exception:  # pragma: no cover - environnement sans dépendance
    _PyPDFLoader = None
    _DirectoryLoader = None

# Alias exportés au module
PyPDFLoader = _PyPDFLoader
DirectoryLoader = _DirectoryLoader


class WebScraper:
    """Scraper web générique avec nettoyage et validation."""

    @staticmethod
    def clean_text(text: str) -> str:
        """Normalise et nettoie un texte brut.

        - NFKC unicode (guillemet/apostrophe typographiques → ASCII)
        - Conserve l'apostrophe simple `'` et la double `"`
        - Supprime caractères indésirables
        - Réduit les espaces multiples
        """
        if not text:
            return ""

        # Normalisation unicode (’ → ', etc.)
        text = unicodedata.normalize("NFKC", text)
        text = text.replace("’", "'").replace("‛", "'").replace("ʻ", "'")

        # Conserver lettres/chiffres/ponctuation de base + apostrophes/quotes
        text = re.sub(r"[^\w\s,.!?;:()\-'\"]", "", text)

        # Espaces multiples -> simple
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def validate_content(content: str, min_length: int = 100) -> bool:
        """Valide la qualité d'un contenu texte simple.

        Critères : longueur minimale + ratio alphabétique ≥ 0.6.
        """
        if not content or len(content) < min_length:
            return False
        alpha_ratio = sum(c.isalpha() for c in content) / len(content)
        return alpha_ratio >= 0.6

    @staticmethod
    def fetch_url(url: str, timeout: int = 15) -> Optional[Dict]:
        """Télécharge et extrait le contenu d'une URL (HTML ou PDF).

        Retourne un dict {title, text, url, length, type} ou None en cas d'échec.
        """
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Medical Research Bot)"}
            response = requests.get(url, timeout=timeout, headers=headers)
            response.raise_for_status()

            # Détection PDF
            content_type = response.headers.get("Content-Type", "").lower()
            mime_type = (mimetypes.guess_type(url)[0] or "").lower()
            if "pdf" in content_type or "pdf" in mime_type:
                return {
                    "title": Path(url).stem,
                    "text": f"PDF Document: {url}",
                    "url": url,
                    "length": 0,
                    "type": "pdf",
                }

            # Parsing HTML
            soup = BeautifulSoup(response.content, "html.parser")
            title_tag = soup.find("title") or soup.find("h1")
            title = title_tag.get_text(strip=True) if title_tag else "Sans Titre"

            content_tags = (
                soup.find_all("article") or soup.find_all("main") or soup.find_all("p")
            )
            paragraphs: List[str] = []
            for tag in content_tags:
                t = tag.get_text(separator=" ", strip=True)
                if len(t) > 50:  # filtre paragraphes trop courts
                    paragraphs.append(t)

            # Joindre avec espace pour éviter les mots collés
            raw_content = " ".join(paragraphs)

            cleaned_title = WebScraper.clean_text(title)
            cleaned_text = WebScraper.clean_text(raw_content)

            if not WebScraper.validate_content(cleaned_text):
                logger.warning(f"Contenu invalide pour l'URL: {url}")
                return None

            return {
                "title": cleaned_title,
                "text": cleaned_text,
                "url": url,
                "length": len(cleaned_text),  # longueur alignée au texte retourné
                "type": "html",
            }
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout lors du scraping de l'URL: {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur réseau lors du téléchargement de l'URL: {url} - {e}")
            return None
        except Exception as e:  # pragma: no cover - garde-fou
            logger.error(f"Erreur inattendue lors du scraping de l'URL: {url} - {e}")
            return None


class PubMedAPI:
    """Client minimal pour l'API PubMed (E-utilities)."""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    @staticmethod
    def search_articles(query: str, max_results: int = 50) -> List[str]:
        """Recherche des articles PubMed par mot-clé, retourne une liste de PMIDs."""
        try:
            search_url = (
                f"{PubMedAPI.BASE_URL}esearch.fcgi?db=pubmed&term={query}&retmax={max_results}&retmode=json"
            )
            response = requests.get(search_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            pmids = data.get("esearchresult", {}).get("idlist", [])
            logger.info(f"PubMed query '{query}': {len(pmids)} résultats.")
            return pmids
        except Exception as e:
            logger.error(f"Erreur lors de la recherche PubMed: {e}")
            return []

    @staticmethod
    def fetch_abstract(pmid: str) -> Optional[Dict]:
        """Récupère le résumé d'un article PubMed par son PMID.

        Retourne {title, text, url, length} ou None si absent/erreur.
        """
        try:
            fetch_url = f"{PubMedAPI.BASE_URL}efetch.fcgi?db=pubmed&id={pmid}&retmode=xml"
            response = requests.get(fetch_url, timeout=10)
            response.raise_for_status()

            from xml.etree import ElementTree as ET

            root = ET.fromstring(response.content)
            nodes = root.findall(".//AbstractText")

            texts: List[str] = []
            for n in nodes:
                t = (n.text or "").strip()
                if not t and len(list(n)) > 0:
                    # Aplatissement simple des sous-noeuds si présents
                    t = "".join((c.text or "") for c in n.iter()).strip()
                if t:
                    texts.append(t)

            if not texts:
                logger.warning(f"Aucun résumé trouvé pour le PMID: {pmid}")
                return None

            abstract_text = " ".join(texts)
            return {
                "title": f"PubMed_{pmid}",
                "text": abstract_text,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "length": len(abstract_text),
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'abstract PubMed: {e}")
            return None


class MedicalTextSplitter:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialise le diviseur de texte médical."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        try:  # import paresseux pour limiter les dépendances
            from langchain_text_splitters import RecursiveCharacterTextSplitter

            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", ". ", " "],
                length_function=len,
            )
        except ImportError as e:  # message clair pour l'utilisateur
            raise ImportError(
                "Veuillez installer `langchain-text-splitters` (pip install langchain-text-splitters)."
            ) from e

    def split_medical_text(self, text: str) -> List[str]:
        """Divise un texte médical en morceaux gérables."""
        return self.splitter.split_text(text)


class PDFLoader:
    """Chargeur PDF spécialisé pour documents médicaux locaux."""

    @staticmethod
    def load_pdfs_from_directory(pdf_dir: str) -> List[Dict]:
        """Charge tous les PDFs d'un répertoire local et retourne des chunks structurés.

        Retour : List[Dict] => {id, title, text, url, length, source}
        """
        try:
            if DirectoryLoader is None or PyPDFLoader is None:
                raise ImportError("langchain-community non installé")

            loader = DirectoryLoader(
                pdf_dir,
                glob="**/*.pdf",
                loader_cls=PyPDFLoader,
            )
            documents = loader.load()

            # Grouper les pages par pdf source
            pdf_groups: Dict[str, List[str]] = {}
            for doc in documents:
                pdf_path = doc.metadata.get("source", "unknown.pdf")
                pdf_groups.setdefault(pdf_path, []).append(doc.page_content)

            # Chunking
            chunked_docs: List[Dict] = []
            doc_id = 0
            for pdf_path, pages in pdf_groups.items():
                full_text = "\n\n".join(pages)
                text_splitter = MedicalTextSplitter()
                chunks = text_splitter.split_medical_text(full_text)
                for chunk in chunks:
                    cleaned = WebScraper.clean_text(chunk)
                    chunked_docs.append(
                        {
                            "id": doc_id,
                            "title": f"{Path(pdf_path).stem} (chunk {doc_id})",
                            "text": cleaned,
                            "url": pdf_path,
                            "length": len(cleaned),
                            "source": "PDF_chunked",
                        }
                    )
                    doc_id += 1

            return chunked_docs
        except Exception as e:  # robustesse vs environnement/deps
            logger.error(f"Erreur lors du chargement des PDFs depuis {pdf_dir}: {e}")
            return []
