import logging
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from routes import router
import logging.config


# Ajouter le répertoire racine
root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from src.core.config import LOGGING_CONFIG

# Configuration du logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Tenglaafi API",
    version="1.0.0",
    description="API pour l'assistant santé Tenglaafi, spécialisé dans la médecine traditionnelle africaine.",
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Middleware pour logger les requêtes
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Requête: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.info(f"Réponse: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Erreur serveur: {e}", exc_info=True)
        raise


# Inclure les routes API
app.include_router(router)

# Monter le répertoire frontend pour servir les fichiers statiques
# html=True permet de servir automatiquement index.html pour le chemin racine
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")


async def show_routes():
    """Événement de démarrage pour afficher les routes disponibles."""
    for r in router.routes:
        print(f"Route trouvée : {r.path} - Méthodes : {r.methods}")
        

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code à exécuter au démarrage
    await show_routes()
    yield
    # Code à exécuter à l'arrêt
    
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.server.main:app", host="0.0.0.0", port=8000)
