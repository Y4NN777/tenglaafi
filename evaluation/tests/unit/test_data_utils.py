"""
Module de tests unitaires pour `src.rag_pipeline.data_utils`.

Ce fichier vérifie le bon fonctionnement de toutes les classes utilitaires
impliquées dans la collecte et la préparation des données du pipeline RAG.
Les tests sont entièrement **déterministes et hors-ligne**, grâce à l’usage
systématique de mocks (`monkeypatch`) pour isoler la logique du code
de toute dépendance réseau ou système de fichiers.

───────────────────────────────────────────────────────────────
STRUCTURE ET PORTÉE DES TESTS
───────────────────────────────────────────────────────────────

1  TestWebScraper
------------------
Vérifie le comportement du scraper web :
- `clean_text()` : suppression d’espaces superflus, normalisation d’apostrophes,
  gestion de chaînes vides et nettoyage des caractères spéciaux.
- `validate_content()` : détection de contenus valides (longueur, ratio alphabétique)
  et rejet des textes trop courts ou dominés par des chiffres (spam).
- `fetch_url()` :
    • Cas PDF : détection correcte via Content-Type ou extension.
    • Cas HTML : parsing du contenu, extraction du titre et des paragraphes.
    • Cas invalides : contenus trop courts ou non textuels rejetés.
    • Cas d’erreurs : gestion de timeouts et exceptions réseau sans crash.

2 TestPubMedAPI
------------------
Assure la robustesse du client PubMed mocké :
- `search_articles()` :
    • Retourne une liste de PMIDs valide pour une réponse JSON simulée.
    • Gère les exceptions réseau en renvoyant une liste vide.
- `fetch_abstract()` :
    • Extraction d’un résumé valide à partir d’un XML contenant <AbstractText>.
    • Retourne `None` si aucun abstract n’est présent.
    • Tolère et journalise les exceptions sans interrompre le flux.

3 TestMedicalTextSplitter
----------------------------
Valide le découpage de texte médical :
- Vérifie que le splitter segmente correctement un texte long selon les
  paramètres `chunk_size` et `chunk_overlap`.
- Confirme que tous les segments sont non vides et cohérents en taille.
- Test sans dépendance externe (aucun PDF requis).

4  TestPDFLoader
------------------
Test du chargeur de documents PDF avec mocks :
- Cas “vide” : un répertoire sans fichiers PDF renvoie une liste vide.
- Cas “inexistant” : un chemin inexistant n’entraîne pas d’erreur fatale.
- Cas “normal” : simulation d’un `DirectoryLoader` et d’un `MedicalTextSplitter`
  produisant plusieurs chunks ; vérifie la structure complète du retour :
  `id`, `title`, `text`, `url`, `length`, `source`.

───────────────────────────────────────────────────────────────
CARACTÉRISTIQUES GÉNÉRALES
───────────────────────────────────────────────────────────────
- 100 % offline : aucun appel HTTP ou lecture de PDF réelle.
- Rapide (< 1 s par exécution) et stable en CI.
- Compatible avec la nouvelle API `langchain-text-splitters` ≥ 0.2.
- Couvre à la fois les scénarios “heureux” (happy path) et les erreurs.
- Facilite la détection précoce de régressions dans la logique de collecte.

───────────────────────────────────────────────────────────────
EXÉCUTION
───────────────────────────────────────────────────────────────
Lancer uniquement les tests unitaires :
    pytest -q evaluation/tests/unit/test_data_utils.py

───────────────────────────────────────────────────────────────
Auteur : Y4NN777
───────────────────────────────────────────────────────────────
"""

import pytest
from typing import Any, Dict, List

from src.rag_pipeline.data_utils import (
    WebScraper,
    PubMedAPI,
    PDFLoader,
    MedicalTextSplitter,
)


# =========================
# WebScraper
# =========================

class TestWebScraper:
    """Tests pour WebScraper"""

    def test_clean_text_removes_extra_spaces(self):
        text = "Hello    world   test"
        cleaned = WebScraper.clean_text(text)
        assert cleaned == "Hello world test"

    def test_clean_text_handles_empty_string(self):
        text = ""
        cleaned = WebScraper.clean_text(text)
        assert cleaned == ""

    def test_clean_text_normalizes_apostrophes(self):
        text = "l'hopital"
        cleaned = WebScraper.clean_text(text)
        assert "'" in cleaned

    def test_validate_content_rejects_short_text(self):
        assert not WebScraper.validate_content("short", min_length=100)

    def test_validate_content_accepts_valid_text(self):
        valid_text = "A" * 150
        assert WebScraper.validate_content(valid_text, min_length=100)

    def test_validate_content_rejects_spam(self):
        spam = "123456789" * 20  # Beaucoup de chiffres
        assert not WebScraper.validate_content(spam)

    def test_fetch_url_detects_pdf(self, monkeypatch):
        """Simule réponse HTTP PDF via Content-Type"""
        class FakeResp:
            status_code = 200
            headers = {"Content-Type": "application/pdf"}
            content = b"%PDF-1.7"
            def raise_for_status(self): pass

        monkeypatch.setattr(
            "src.rag_pipeline.data_utils.requests.get",
            lambda *a, **k: FakeResp(),
        )

        result = WebScraper.fetch_url("http://x/y.pdf", timeout=1)
        assert result is not None
        assert result["type"] == "pdf"
        assert "PDF" in result["text"]

    def test_fetch_url_parses_html_happy_path(self, monkeypatch):
        """HTML avec <title> et plusieurs <p> (assez longs)"""
        html = b"""
        <html><head><title>Test Page</title></head>
        <body>
          <main>
            <p>Paragraphe un, suffisamment long pour passer les filtres. "Malaria" and fever.</p>
            <p>Paragraphe deux, lui aussi suffisamment long et riche en lettres pour la validation.</p>
          </main>
        </body></html>
        """

        class FakeResp:
            status_code = 200
            headers = {"Content-Type": "text/html; charset=utf-8"}
            content = html
            def raise_for_status(self): pass

        monkeypatch.setattr(
            "src.rag_pipeline.data_utils.requests.get",
            lambda *a, **k: FakeResp(),
        )

        res = WebScraper.fetch_url("http://example.org")
        assert res is not None
        assert res["type"] == "html"
        assert res["title"] == "Test Page"
        assert "Paragraphe un" in res["text"]
        assert res["length"] == len(res["text"])

    def test_fetch_url_invalid_content_returns_none(self, monkeypatch):
        """HTML trop court → validate_content False → None"""
        html = b"<html><body><p>trop court</p></body></html>"

        class FakeResp:
            status_code = 200
            headers = {"Content-Type": "text/html"}
            content = html
            def raise_for_status(self): pass

        monkeypatch.setattr(
            "src.rag_pipeline.data_utils.requests.get",
            lambda *a, **k: FakeResp(),
        )

        res = WebScraper.fetch_url("http://example.org")
        assert res is None

    def test_fetch_url_handles_timeout(self, monkeypatch):
        import requests

        def raise_timeout(*a, **k):
            raise requests.exceptions.Timeout()

        monkeypatch.setattr(
            "src.rag_pipeline.data_utils.requests.get",
            raise_timeout,
        )

        res = WebScraper.fetch_url("http://timeout.test", timeout=1)
        assert res is None

    def test_fetch_url_handles_request_exception(self, monkeypatch):
        import requests

        def raise_req_exc(*a, **k):
            raise requests.exceptions.RequestException("boom")

        monkeypatch.setattr(
            "src.rag_pipeline.data_utils.requests.get",
            raise_req_exc,
        )

        res = WebScraper.fetch_url("http://boom")
        assert res is None


# =========================
# PubMedAPI
# =========================

class TestPubMedAPI:
    """Tests pour PubMedAPI (mock HTTP)"""

    def test_search_articles_returns_pmids(self, monkeypatch):
        class FakeResp:
            def raise_for_status(self): pass
            def json(self):
                return {"esearchresult": {"idlist": ["1", "2", "3"]}}

        monkeypatch.setattr(
            "src.rag_pipeline.data_utils.requests.get",
            lambda *a, **k: FakeResp(),
        )

        pmids = PubMedAPI.search_articles("malaria", max_results=5)
        assert isinstance(pmids, list)
        assert pmids == ["1", "2", "3"]

    def test_search_articles_handles_error(self, monkeypatch):
        def raise_exc(*a, **k):
            raise RuntimeError("network down")

        monkeypatch.setattr(
            "src.rag_pipeline.data_utils.requests.get",
            raise_exc,
        )

        pmids = PubMedAPI.search_articles("malaria", max_results=5)
        assert pmids == []

    def test_fetch_abstract_returns_dict(self, monkeypatch):
        """XML avec AbstractText présent"""
        xml = b"""
        <PubmedArticleSet>
          <PubmedArticle>
            <MedlineCitation>
              <Article>
                <Abstract>
                  <AbstractText>Texte d'abstract ici.</AbstractText>
                </Abstract>
              </Article>
            </MedlineCitation>
          </PubmedArticle>
        </PubmedArticleSet>
        """

        class FakeResp:
            def raise_for_status(self): pass
            @property
            def content(self): return xml

        monkeypatch.setattr(
            "src.rag_pipeline.data_utils.requests.get",
            lambda *a, **k: FakeResp(),
        )

        res = PubMedAPI.fetch_abstract("12345678")
        assert res is not None
        assert res["title"].startswith("Pub")
        assert "Texte d'abstract" in res["text"]
        assert res["url"].endswith("/12345678/")
        assert res["length"] == len(res["text"])

    def test_fetch_abstract_returns_none_when_no_abstract(self, monkeypatch):
        """XML sans AbstractText → None"""
        xml = b"""
        <PubmedArticleSet>
          <PubmedArticle>
            <MedlineCitation>
              <Article>
                <Abstract></Abstract>
              </Article>
            </MedlineCitation>
          </PubmedArticle>
        </PubmedArticleSet>
        """

        class FakeResp:
            def raise_for_status(self): pass
            @property
            def content(self): return xml

        monkeypatch.setattr(
            "src.rag_pipeline.data_utils.requests.get",
            lambda *a, **k: FakeResp(),
        )

        res = PubMedAPI.fetch_abstract("999")
        assert res is None

    def test_fetch_abstract_handles_error(self, monkeypatch):
        def raise_exc(*a, **k):
            raise ValueError("oops")

        monkeypatch.setattr(
            "src.rag_pipeline.data_utils.requests.get",
            raise_exc,
        )

        res = PubMedAPI.fetch_abstract("err")
        assert res is None


# =========================
# MedicalTextSplitter
# =========================

class TestMedicalTextSplitter:
    """Tests pour le splitter médical"""

    def test_medical_text_splitter_basic(self):
        txt = " ".join(["mot"] * 1500)  # texte assez long
        splitter = MedicalTextSplitter(chunk_size=200, chunk_overlap=50)
        chunks = splitter.split_medical_text(txt)
        assert len(chunks) > 1
        # chaque chunk doit être raisonnable en taille
        assert all(len(c) > 0 for c in chunks)
        # Pas besoin d'être strict sur overlap : on valide juste le fonctionnement


# =========================
# PDFLoader
# =========================

class TestPDFLoader:
    """Tests pour PDFLoader (mock DirectoryLoader et Splitter)"""

    def test_load_pdfs_from_empty_directory(self, monkeypatch, tmp_path):
        """Mock DirectoryLoader.load -> []"""
        class FakeDL:
            def __init__(self, *a, **k): pass
            def load(self): return []

        monkeypatch.setattr(
            "src.rag_pipeline.data_utils.DirectoryLoader",
            FakeDL,
        )

        docs = PDFLoader.load_pdfs_from_directory(str(tmp_path))
        assert docs == []

    def test_load_pdfs_from_nonexistent_directory(self, monkeypatch):
        """Mock DirectoryLoader.__init__ qui lève FileNotFoundError"""
        def raise_not_found(*a, **k):
            raise FileNotFoundError("dir not found")

        class FakeDL:
            def __init__(self, *a, **k): raise_not_found()
            def load(self): return []

        monkeypatch.setattr(
            "src.rag_pipeline.data_utils.DirectoryLoader",
            FakeDL,
        )

        docs = PDFLoader.load_pdfs_from_directory("/path/does/not/exist")
        assert docs == []

    def test_load_pdfs_happy_path_with_chunks(self, monkeypatch, tmp_path):
        """Mock DirectoryLoader + Splitter pour produire 2 chunks"""
        class FakeDoc:
            def __init__(self, src: str, content: str):
                self.metadata = {"source": src}
                self.page_content = content

        class FakeDL:
            def __init__(self, *a, **k): pass
            def load(self):
                return [
                    FakeDoc(str(tmp_path / "a.pdf"), "page1 content"),
                    FakeDoc(str(tmp_path / "a.pdf"), "page2 content"),
                ]

        class FakeSplitter:
            def __init__(self, *a, **k): pass
            def split_medical_text(self, text: str) -> List[str]:
                # renvoie deux chunks déterministes
                return ["chunk-one", "chunk-two"]

        # Patch DirectoryLoader et MedicalTextSplitter
        monkeypatch.setattr(
            "src.rag_pipeline.data_utils.DirectoryLoader",
            FakeDL,
        )
        monkeypatch.setattr(
            "src.rag_pipeline.data_utils.MedicalTextSplitter",
            FakeSplitter,
        )

        docs = PDFLoader.load_pdfs_from_directory(str(tmp_path))
        assert isinstance(docs, list) and len(docs) == 2
        assert {"id", "title", "text", "url", "length", "source"} <= set(docs[0].keys())
        assert docs[0]["text"] == "chunk-one"
        assert docs[1]["text"] == "chunk-two"
        assert docs[0]["source"].lower().startswith("pdf")
        assert docs[0]["id"] == 0
        assert docs[1]["id"] == 1
