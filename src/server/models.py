from pydantic import BaseModel, Field,  EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# Modèle pour la requête envoyée à /query
class QueryRequest(BaseModel):
    """Schéma pour la requête de question utilisateur"""
    question: str = Field(..., example="Quels sont les symptômes du paludisme ?")
    top_k: Optional[int] = Field(3, ge=1, le=10, example=3)

# Modèle pour la réponse renvoyée
class QueryResponse(BaseModel):
    """Schéma pour la réponse renvoyée à l'utilisateur"""
    answer: str
    sources: Optional[List[Dict[str, Any]]] = None

