from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from .routes import router
import logging

# Configuration du logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialisation de l'application FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API de TengLaafi - RAG médical intelligent"
)

# Middleware CORS (pour autoriser ton frontend à communiquer)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # à restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging de chaque requête
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logging.info(f"Requête reçue : {request.method} {request.url}")
    response = await call_next(request)
    logging.info(f"Réponse envoyée : {response.status_code}")
    return response

# Enregistrement des routes principales
app.include_router(router)

# Point d’entrée principal (pour uvicorn)
if __name__ == "__main__":
    import importlib
    try:
        uvicorn = importlib.import_module("uvicorn")
    except ImportError:
        raise SystemExit("uvicorn n'est pas installé. Installez-le avec : pip install 'uvicorn[standard]'")
    uvicorn.run("src.server.main:app", host="0.0.0.0", port=8000, reload=True)
