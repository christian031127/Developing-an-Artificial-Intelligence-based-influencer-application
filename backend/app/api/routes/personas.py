from fastapi import APIRouter
from app.services.persona_registry import list_personas

router = APIRouter()

@router.get("/personas")
def personas():
    return [p.model_dump() for p in list_personas()]
