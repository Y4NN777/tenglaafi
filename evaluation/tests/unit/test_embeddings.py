# evaluation/tests/unit/test_embeddings_unit.py
import numpy as np
import pytest

# Points de patch selon ton module
PATCH_ST = "src.rag_pipeline.embeddings.SentenceTransformer"

from src.rag_pipeline.embeddings import (
    EmbeddingManager,
    get_embedding_manager,
    embed_query as embed_query_fn,
    embed_texts as embed_texts_fn,
)

# ─────────────────────────────────────────────────────────────
# Fake SentenceTransformer déterministe (aucun accès réseau)
# ─────────────────────────────────────────────────────────────
class FakeST:
    def __init__(self, name: str):
        self._name = name
        self._dim = 6  # petite dim pour tests

    def get_sentence_embedding_dimension(self) -> int:
        return self._dim

    def encode(
        self,
        texts,
        batch_size: int = 32,
        show_progress_bar: bool = False,
        convert_to_numpy: bool = True,
        normalize_embeddings: bool = True,
    ):
        # Fabrique des vecteurs déterministes en fonction de l'index
        def mk(seed: int):
            v = np.arange(seed, seed + self._dim, dtype=np.float32)
            if normalize_embeddings:
                v = v / np.linalg.norm(v)
            return v

        if isinstance(texts, (list, tuple)):
            arr = np.stack([mk(i + 1) for i, _ in enumerate(texts)], axis=0)
            return arr
        # Non utilisé par notre code (on passe toujours une liste), couvre quand même
        return mk(1)

# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def patch_sentence_transformer(monkeypatch):
    monkeypatch.setattr(PATCH_ST, lambda name: FakeST(name))

@pytest.fixture
def manager() -> EmbeddingManager:
    return EmbeddingManager(model_name="fake-mini")

# ─────────────────────────────────────────────────────────────
# Tests EmbeddingManager (unitaires, déterministes)
# ─────────────────────────────────────────────────────────────
class TestEmbeddingManagerUnit:
    def test_init_sets_model_and_dimension(self, manager):
        assert manager.model is not None
        assert isinstance(manager.dimension, int) and manager.dimension == 6

    def test_embed_query_empty_returns_empty_array(self, manager):
        v = manager.embed_query("")
        assert isinstance(v, np.ndarray)
        assert v.size == 0

    def test_embed_query_shape_and_norm(self, manager):
        v = manager.embed_query("paludisme")
        assert v.shape == (manager.dimension,)
        # embeddings normalisés → norme ≈ 1
        norm = np.linalg.norm(v)
        assert 0.99 <= norm <= 1.01

    def test_embed_texts_batch_shapes_and_distinct(self, manager):
        texts = ["a", "b", "c"]
        M = manager.embed_texts(texts, batch_size=2, show_progress=False)
        assert M.shape == (len(texts), manager.dimension)
        # vecteurs différents (dépendent de l'index seed)
        assert not np.allclose(M[0], M[1])

    def test_embed_texts_empty_list(self, manager):
        M = manager.embed_texts([], show_progress=False)
        # le code renvoie np.array([]) → shape (0,)
        assert isinstance(M, np.ndarray)
        assert M.shape == (0,)

    def test_compute_similarity_on_normalized_vectors(self, manager):
        # Avec FakeST, on sait exactement ce que renvoie encode
        q = manager.embed_query("q")
        D = manager.embed_texts(["d1", "d2"], show_progress=False)
        sims = manager.compute_similarity(q, D)
        assert sims.shape == (2,)
        # bornes cosinus (vecteurs unitaires)
        assert np.all(sims <= 1.0) and np.all(sims >= -1.0)
        # Les deux scores sont différents (vecteurs différents)
        assert sims[0] != sims[1]

    def test_compute_similarity_raises_on_shape_mismatch(self, manager):
        q = np.ones((manager.dimension,), dtype=np.float32)
        bad = np.ones((3, manager.dimension + 1), dtype=np.float32)
        with pytest.raises(Exception):
            manager.compute_similarity(q, bad)

    def test_init_raises_when_model_fails(self, monkeypatch):
        class Boom:
            def __init__(self, *_a, **_k):
                raise RuntimeError("load failed")
        monkeypatch.setattr(PATCH_ST, Boom)
        with pytest.raises(RuntimeError):
            EmbeddingManager(model_name="boom")

# ─────────────────────────────────────────────────────────────
# Tests du singleton et des wrappers (API prête à intégrer)
# ─────────────────────────────────────────────────────────────
def test_singleton_and_wrappers(monkeypatch):
    import src.rag_pipeline.embeddings as emb
    # reset singleton proprement
    emb._embedding_manager = None
    monkeypatch.setattr(PATCH_ST, lambda name: FakeST(name))

    m1 = get_embedding_manager()
    m2 = get_embedding_manager()
    assert m1 is m2  # même instance -> pas de double chargement en prod

    q_vec = emb.embed_query("abc")
    d_vecs = emb.embed_texts(["x", "y"])
    # les wrappers doivent renvoyer des listes (conversion .tolist())
    assert isinstance(q_vec, list) and all(isinstance(x, float) for x in q_vec)
    assert isinstance(d_vecs, list) and isinstance(d_vecs[0], list)
