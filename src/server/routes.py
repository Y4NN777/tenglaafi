from fastapi import APIRouter, HTTPException
from src.server.models import QueryRequest, QueryResponse
from src.rag_pipeline.rag import RAGPipeline

router = APIRouter()

# Initialisation du moteur RAG
rag = RAGPipeline()

@router.get("/health")
async def health_check():
    """Vérifie que le backend et le pipeline RAG fonctionnent."""
    return {"status": "OK", "message": "TengLaafi API est opérationnelle."}


@router.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Reçoit une question utilisateur et renvoie une réponse générée via RAG."""
    question = request.question.strip()

    if len(question) < 3:
        raise HTTPException(status_code=400, detail="La question est trop courte.")

    try:
        response = rag.query(question, top_k=request.top_k)
        return QueryResponse(answer=response["answer"], sources=response.get("sources"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
