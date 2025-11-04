from typing import List, Dict

class RAGPipeline:
    """Pipeline RAG mock pour test API"""

    def __init__(self):
        print(" RAGPipeline initialisé (mock)")

    def query(self, question: str, top_k: int = 3) -> Dict:
        answer = f"Réponse simulée à la question : '{question}'"
        sources = [{"title": f"Source {i+1}", "url": f"http://example.com/{i+1}"} for i in range(top_k)]
        return {"answer": answer, "sources": sources}
