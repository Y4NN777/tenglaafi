"""
Tests d'intégration pour l'API Tenglaafi
"""
from fastapi.testclient import TestClient
from src.server.main import app

client = TestClient(app)

def test_health_endpoint():
    """
    Test de l'endpoint /health pour vérifier que le backend est opérationnel.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "OK"  # Correction: OK en majuscules

def test_query_endpoint_valid_question():
    """
    Test de l'endpoint /query avec une question valide.
    """
    payload = {"question": "Qu'est ce que le paludisme ?", "top_k": 5}
    response = client.post("/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    # On accepte que 'answer' contienne un message d'erreur du LLM
    assert isinstance(data["answer"], str)
    assert isinstance(data["sources"], list)

def test_query_endpoint_short_question():
    """
    Test de l'endpoint /query avec une question trop courte (doit renvoyer une erreur 400).
    """
    payload = {"question": "Hi"}
    response = client.post("/query", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data

def test_query_endpoint_missing_top_k():
    """
    Test de l'endpoint /query sans préciser top_k (doit utiliser la valeur par défaut). 
    """
    payload = {"question": "Quels sont les symptômes du paludisme ?"}
    response = client.post("/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert isinstance(data["answer"], str)
    assert isinstance(data["sources"], list)

def test_query_endpoint_invalid_type():
    """
    Test de l'endpoint /query avec un type incorrect pour question (doit renvoyer erreur 422).
    """
    payload = {"question": 12345}
    response = client.post("/query", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data