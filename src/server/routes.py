from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from models import QueryRequest, QueryResponse

import sys
from pathlib import Path

# Ajouter le répertoire racine
root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from src.rag_pipeline.rag import RAGPipeline

router = APIRouter()

# Initialisation du moteur RAG
rag = RAGPipeline()

    

from fastapi import APIRouter, Response

router = APIRouter()

@router.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    """Vérifie que le backend et le pipeline RAG fonctionnent."""
    return Response(
        content='{"status":"OK","message":"TengLaafi API est opérationnelle."}',
        media_type="application/json",
        status_code=200
    )



@router.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Reçoit une question utilisateur et renvoie une réponse générée via RAG."""
    question = request.question.strip()

    if len(question) < 3:
        raise HTTPException(status_code=400, detail="La question est trop courte.")

    try:
        # rag.query retourne un tuple (answer, sources)
        answer, sources = rag.query(question, top_k=request.top_k, return_sources=True)
        return QueryResponse(answer=answer, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
