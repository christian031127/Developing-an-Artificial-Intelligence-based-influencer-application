# backend/app/api/routes/images.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Tuple, Optional
from ...services.ai_image import build_prompt, generate_openai_img2img
from ...core.db import db
from bson import ObjectId
import uuid
from urllib.parse import urlparse

router = APIRouter(prefix="/api/images", tags=["images"])

# --- KÉRÉS / VÁLASZ sémák ---
class ImageReq(BaseModel):
    prompt: str | None = None          # ha megadsz szabad promptot, azzal dolgozunk
    personaId: str | None = None       # különben persona + topic kell
    topic: str | None = None
    trendTags: List[str] | None = None
    negative_prompt: str | None = None # (OpenAI editnél nem használjuk)
    count: int = 1                     # maximum 3 képet generálunk

class ImageRespItem(BaseModel):
    id: str
    url: str

class ImageResp(BaseModel):
    images: List[ImageRespItem]

# --- Segéd: persona portré → konténerbeli lokális útvonal ---
def _resolve_init_path(p: dict) -> Optional[str]:
    """
    Magyar magyarázat:
    - Előnyben a feltöltött fájl (filename → /uploads/characters/...).
    - Ha csak URL van, és az /uploads/...-ra mutat, konténerben /app + path.
    - Kezeli az új (ref_image_url) és a régi (imageUrl) mezőket is, hogy visszafelé kompatibilis legyen.
    """
    # Új séma: belső mentett fájlnév
    if p.get("filename"):
        return f"/app/uploads/characters/{p['filename']}"

    # Új séma: ref_image_url
    if p.get("ref_image_url"):
        parsed = urlparse(p["ref_image_url"])
        if parsed.path.startswith("/uploads/"):
            return "/app" + parsed.path

    # Régi séma: imageUrl
    if p.get("imageUrl"):
        parsed = urlparse(p["imageUrl"])
        if parsed.path.startswith("/uploads/"):
            return "/app" + parsed.path

    return None

# --- Segéd: prompt + init_path feloldása ---
def _resolve_prompt_and_init_path(req: ImageReq) -> Tuple[str, Optional[str]]:
    """
    - Ha personaId + topic jön: persona alapján építünk promptot, portréval (img2img).
    - Ha 'prompt' jön: azt használjuk, de img2img-hez init kép kell → ilyenkor hibát dobunk.
      (Ez az endpoint kifejezetten persona+topic img2img.)
    """
    if not req.prompt and req.personaId and req.topic:
        p = db.personas.find_one({"_id": ObjectId(req.personaId)})
        if not p:
            raise HTTPException(status_code=400, detail="personaId not found")

        # KOMPAT: a régi build_prompt megmarad (benne van a 'no text' guardrail)
        pos, _neg = build_prompt(
            persona_name=p.get("name"),
            topic=req.topic,
            trend_tags=(req.trendTags or []),
        )
        init_path = _resolve_init_path(p)
        if not init_path:
            raise HTTPException(400, "Persona portrait not found; cannot run img2img.")
        return pos, init_path

    if req.prompt:
        # Ez az endpoint csak persona+topic img2img-re való.
        raise HTTPException(400, "This endpoint requires personaId+topic (img2img).")

    raise HTTPException(400, "Provide 'personaId' and 'topic'.")

# --- FŐ ENDPOINT: OpenAI img2img 256x256 + 4:5 padosítás (olcsó mód) ---
@router.post("/generate", response_model=ImageResp)
async def generate_image(req: ImageReq):
    """
    Magyar magyarázat:
    - Persona + topic alapján építünk promptot.
    - A persona portréja lesz az 'init image' (img2img).
    - OpenAI Images Edit hívás: 256x256 (olcsó), majd 4:5 padosítás 256x320-ra (torzítás nélkül).
    """
    prompt, init_path = _resolve_prompt_and_init_path(req)

    results: List[ImageRespItem] = []
    for _ in range(min(req.count or 1, 3)):
        _img_id, url = await generate_openai_img2img(
            init_image_path=init_path,
            prompt=prompt,
            size="1024x1024",       # olcsó
            pad_to_portrait=True, # 4:5 padosítás (1024x1280)
        )
        results.append(ImageRespItem(id=str(uuid.uuid4()), url=url))

    return ImageResp(images=results)
