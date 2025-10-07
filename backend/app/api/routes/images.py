from http.client import HTTPException
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from ...services.ai_image import generate_sdxl, build_prompt, generate_sdxl_img2img
from ...core.db import db
from bson import ObjectId
from pathlib import Path

router = APIRouter(prefix="/api/images", tags=["images"])

class ImageReq(BaseModel):
    prompt: str | None = None
    personaId: str | None = None
    topic: str | None = None
    trendTags: List[str] | None = None
    negative_prompt: str | None = None
    count: int = 1

class ImageRespItem(BaseModel):
    id: str
    url: str

class ImageResp(BaseModel):
    images: List[ImageRespItem]

def resolve_prompt_and_init_path(req: ImageReq):
    """
    Helper to resolve prompt, negative prompt, and init_path based on the request.
    """
    prompt: str | None = None
    negative: str | None = None
    init_path: str | None = None

    if not req.prompt and req.personaId and req.topic:
        p = db.personas.find_one({"_id": ObjectId(req.personaId)})
        if not p:
            raise HTTPException(status_code=400, detail="personaId not found")

        pos, neg = build_prompt(
            persona_name=p.get("name"),
            topic=req.topic,
            trend_tags=(req.trendTags or []),
        )
        prompt = pos
        negative = req.negative_prompt or neg

        if p.get("filename"):
            init_path = f"/app/uploads/characters/{p['filename']}"
        elif p.get("imageUrl"):
            from urllib.parse import urlparse
            parsed = urlparse(p["imageUrl"])
            if parsed.path.startswith("/uploads/"):
                init_path = "/app" + parsed.path
    elif req.prompt:
        prompt = req.prompt
        negative = req.negative_prompt
    else:
        raise HTTPException(status_code=400, detail="Provide either 'prompt' or ('personaId' and 'topic').")

    return prompt, negative, init_path

@router.post("/generate", response_model=ImageResp)
async def generate_image(req: ImageReq):
    results: list[ImageRespItem] = []

    prompt, negative, init_path = resolve_prompt_and_init_path(req)

    for _ in range(min(req.count or 1, 3)):
        if init_path and Path(init_path).exists():
            img_id, url = await generate_sdxl_img2img(
                init_image_path=init_path,
                prompt=prompt,
                negative_prompt=negative,
                strength=0.7,
                guidance=7.5,
                steps=30,
            )
        else:
            img_id, url = await generate_sdxl(
                prompt=prompt,
                negative_prompt=negative,
                width=896,
                height=1152,
                steps=28,
                guidance=7.5,
            )

        results.append(ImageRespItem(id=str(img_id), url=url))

    return ImageResp(images=results)
