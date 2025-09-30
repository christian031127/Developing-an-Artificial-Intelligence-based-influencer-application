from pydantic import BaseModel
from typing import List, Dict

class Persona(BaseModel):
    id: str
    name: str
    tone: str
    topics: List[str]
    visual: Dict[str, str]  # e.g. {"palette":"indigo-amber","watermark":"FitAI"}
    brand_tag: str = "fitai"
