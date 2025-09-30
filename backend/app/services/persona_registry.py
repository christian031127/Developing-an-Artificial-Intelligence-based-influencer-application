from typing import List, Optional
from app.models.persona import Persona

_PERSONAS: List[Persona] = [
    Persona(
        id="fit_girl_v1",
        name="Maya",
        tone="friendly, upbeat, concise",
        topics=["workout","lifestyle","nutrition"],
        visual={"palette":"indigo-amber","watermark":"FitAI"},
        brand_tag="fitai",
    ),
    Persona(
        id="finance_guy_v1",
        name="Ethan",
        tone="calm, practical, no-hype",
        topics=["budgeting","investing","productivity"],
        visual={"palette":"cyan-violet","watermark":"FinAI"},
        brand_tag="finai",
    ),
    Persona(
        id="lifestyle_creator_v1",
        name="Ella",
        tone="warm, aesthetic, minimal",
        topics=["morning routine","minimalism","wellness"],
        visual={"palette":"rose-amber","watermark":"EllaAI"},
        brand_tag="ellai",
    ),
]

def list_personas() -> List[Persona]:
    return _PERSONAS

def get_persona(pid: str) -> Optional[Persona]:
    for p in _PERSONAS:
        if p.id == pid:
            return p
    return None
