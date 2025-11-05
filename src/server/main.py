# import logging
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from .models import QueryRequest, QueryResponse
# from src.rag_pipeline.rag import RAGPipeline
# import traceback
# from .routes import router

# # Configuration du logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = FastAPI(title="Tenglaafi API", version="1.0.0")



# # Middleware CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Initialisation du pipeline RAG
# rag_pipeline = RAGPipeline()

# # Middleware pour logger les requêtes
# @app.middleware("http")
# async def log_requests(request, call_next):
#     logger.info(f"Requête reçue : {request.method} {request.url}")
#     response = await call_next(request)
#     logger.info(f"Réponse envoyée : {response.status_code}")
#     return response

# # Enregistrement des routes principales
# app.include_router(router)


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .models import QueryRequest, QueryResponse
from src.rag_pipeline.rag import RAGPipeline
import traceback

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Tenglaafi API", version="1.0.0")

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation du pipeline RAG
rag_pipeline = RAGPipeline()

# Middleware pour logger les requêtes
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Requête reçue : {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Réponse envoyée : {response.status_code}")
    return response

@app.get("/health")
def health_check():
    """Endpoint de santé pour vérifier que l'API fonctionne."""
    return {"status": "OK"}

@app.post("/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest):
    """
    Endpoint principal pour répondre aux questions médicales.
    """
    try:
        # Validation de la longueur de la question
        if len(request.question.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="La question doit contenir au moins 10 caractères"
            )
        
        logger.info(f"Question reçue: {request.question[:50]}...")
        
        # CORRECTION : Utiliser query() au lieu de answer_query()
        answer, sources = rag_pipeline.query(
            question=request.question,
            k=request.top_k,
            return_sources=True
        )
        
        logger.info(f"Réponse générée avec {len(sources) if sources else 0} sources")
        
        return QueryResponse(answer=answer, sources=sources)
    
    except HTTPException:
        # Re-lever les HTTPException sans les modifier
        raise
    
    except Exception as e:
        # Logger l'erreur complète avec la stack trace
        logger.error(f"Erreur lors du traitement de la requête: {str(e)}")
        logger.error(f"Stack trace:\n{traceback.format_exc()}")
        
        # Afficher aussi dans la console pour le debug
        print(f"\nERREUR DÉTAILLÉE:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        print(f"Stack trace:\n{traceback.format_exc()}")
        
        # Retourner une erreur 500 avec les détails complets
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)