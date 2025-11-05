from fastapi.testclient import TestClient
from src.server.main import app

client = TestClient(app)


def test_health_check():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "OK"


def test_query_endpoint(monkeypatch):
    # Mock du pipeline RAG pour tests rapides
    class DummyRAG:
        def query(self, q, top_k=3):
            return {"answer": "Réponse test", "sources": []}

    from src.server import routes

    routes.rag = DummyRAG()

    r = client.post("/query", json={"question": "Symptômes du paludisme"})
    assert r.status_code == 200
    assert "answer" in r.json()
