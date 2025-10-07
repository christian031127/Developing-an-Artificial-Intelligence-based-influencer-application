import os
from io import BytesIO
from zipfile import ZipFile
from uuid import uuid4
from typing import List, Optional, Literal
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from bson import ObjectId

from app.core.settings import settings
from app.core.db import db
from app.core.files import UPLOAD_DIR

from app.services.ai_text import gen_caption_and_tags
from app.services.ai_image import generate_sdxl_img2img, build_prompt

router = APIRouter(tags=["drafts"])

class Idea(BaseModel):
    id: str
    title: str
    category: Literal["workout", "meal", "lifestyle"]

class DraftCreate(BaseModel):
    ideaId: Optional[str] = None
    title: str
    category: Literal["workout","meal","lifestyle"] = "lifestyle"
    caption: str = ""
    hashtags: List[str] = Field(default_factory=list)
    customText: Optional[str] = None
    personaId: str

class Draft(DraftCreate):
    id: str
    status: Literal["draft","approved"] = "draft"
    previewUrl: Optional[str] = None
    filename: Optional[str] = None

def _serialize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc

@router.get("/ideas", response_model=List[Idea])
def list_ideas():
    return [
        {"id": "i1", "title": "Leg day routine", "category": "workout"},
        {"id": "i2", "title": "High-protein breakfast bowl", "category": "meal"},
        {"id": "i3", "title": "Active rest day walk", "category": "lifestyle"},
    ]

@router.get("/drafts", response_model=List[Draft])
def get_drafts():
    return [_serialize(d) for d in db.drafts.find().sort("_id", -1)]

def _load_persona_or_404(persona_id: str) -> dict:
    try:
        p = db.personas.find_one({"_id": ObjectId(persona_id)})
    except Exception:
        p = None
    if not p:
        raise HTTPException(400, "personaId is invalid or not found")
    return p

@router.post("/drafts", response_model=Draft)
async def create_draft(body: DraftCreate):
    persona = _load_persona_or_404(body.personaId)

    # 1) Caption + hashtags (AI → fallback)
    caption = (body.caption or "").strip()
    hashtags = list(body.hashtags or [])
    if not caption or not hashtags:
        try:
            tone = persona.get("tone") or "friendly, concise"
            brand_tag = persona.get("brand_tag") or "brand"
            cap, tags = await gen_caption_and_tags(
                topic=body.title,
                category=body.category,
                brand_tag=brand_tag,
                custom_text=body.customText or tone
            )
            caption = caption or cap
            hashtags = hashtags or tags
        except Exception:
            caption = caption or "Save this for later! 💡"
            hashtags = hashtags or ["post","daily","ideas","trending"]

    # 2) Persona portré → init_path
    init_path = None
    if persona.get("filename"):
        init_path = f"/app/uploads/characters/{persona['filename']}"
    elif persona.get("imageUrl"):
        from urllib.parse import urlparse
        parsed = urlparse(persona["imageUrl"])
        if parsed.path.startswith("/uploads/"):
            init_path = "/app" + parsed.path
    if not init_path:
        raise HTTPException(400, "Persona portrait not found; cannot run img2img.")

    # 3) Prompt (persona + topic + trendTags≈hashtags)
    positive, negative = build_prompt(
        persona_name=persona.get("name"),
        topic=body.title,
        trend_tags=hashtags
    )

    # 4) SDXL img2img (HF serverless)
    try:
        _, url = await generate_sdxl_img2img(
            init_image_path=init_path,
            prompt=positive,
            negative_prompt=negative,
            strength=0.7,
            guidance=7.5,
            steps=30,
        )
    except HTTPException as e:
        # ideiglenes debug
        print("IMG2IMG ERROR:", e.detail)
        raise

    # 5) Mentés
    doc = body.model_dump()
    doc.update({
        "caption": caption,
        "hashtags": hashtags,
        "status": "draft",
        "previewUrl": url,
    })
    res = db.drafts.insert_one(doc)
    return Draft(id=str(res.inserted_id), **doc)

@router.patch("/drafts/{draft_id}", response_model=Draft)
def patch_draft(draft_id: str, body: dict):
    allowed = {"personaId","caption","hashtags","title","category","customText"}
    update = {k:v for k,v in (body or {}).items() if k in allowed}
    if not update:
        raise HTTPException(400, "No updatable fields provided")
    if "personaId" in update:
        _load_persona_or_404(update["personaId"])  # validáljuk
    doc = db.drafts.find_one_and_update(
        {"_id": ObjectId(draft_id)}, {"$set": update}, return_document=True
    )
    if not doc:
        raise HTTPException(404, "Draft not found")
    return Draft(**_serialize(doc))

@router.post("/drafts/{draft_id}/approve", response_model=Draft)
def approve_draft(draft_id: str):
    doc = db.drafts.find_one_and_update(
        {"_id": ObjectId(draft_id)}, {"$set": {"status": "approved"}}, return_document=True
    )
    if not doc:
        raise HTTPException(404, "Draft not found")
    return Draft(**_serialize(doc))

@router.delete("/drafts/{draft_id}")
def delete_draft(draft_id: str):
    ok = db.drafts.delete_one({"_id": ObjectId(draft_id)}).deleted_count
    if not ok:
        raise HTTPException(404, "Draft not found")
    return {"ok": True}

@router.post("/drafts/{draft_id}/regen_caption", response_model=Draft)
async def regen_caption(draft_id: str):
    d = db.drafts.find_one({"_id": ObjectId(draft_id)})
    if not d:
        raise HTTPException(404, "Draft not found")

    persona = _load_persona_or_404(d.get("personaId"))
    tone = persona.get("tone") or "friendly, concise"
    brand_tag = persona.get("brand_tag") or "brand"

    try:
        cap, tags = await gen_caption_and_tags(
            topic=d.get("title",""),
            category=d.get("category","lifestyle"),
            brand_tag=brand_tag,
            custom_text=d.get("customText") or tone
        )
    except Exception:
        cap = (d.get("title") or "New post") + " — save it!"
        tags = d.get("hashtags") or [brand_tag]

    doc = db.drafts.find_one_and_update(
        {"_id": ObjectId(draft_id)}, {"$set": {"caption": cap, "hashtags": tags}}, return_document=True
    )
    return Draft(**_serialize(doc))

@router.post("/drafts/{draft_id}/regen_image", response_model=Draft)
async def regen_image(draft_id: str):
    d = db.drafts.find_one({"_id": ObjectId(draft_id)})
    if not d:
        raise HTTPException(404, "Draft not found")

    persona = _load_persona_or_404(d.get("personaId"))
    style = d.get("imageStyle") or persona.get("default_image_style") or "clean"
    watermark = persona.get("watermark") or persona.get("name") or "Studio"
    subtitle = "#" + (d.get("hashtags",[None])[0] or (persona.get("brand_tag") or "brand"))

    img_bytes = render_composite(style, title=d.get("title",""), subtitle=subtitle, watermark=watermark)

    old = d.get("filename")
    if old:
        old_path = os.path.join(UPLOAD_DIR, old)
        if os.path.exists(old_path):
            try: os.remove(old_path)
            except: pass

    fname = f"{uuid4()}.jpg"
    out_path = os.path.join(UPLOAD_DIR, fname)
    with open(out_path, "wb") as f:
        f.write(img_bytes)

    doc = db.drafts.find_one_and_update(
        {"_id": ObjectId(draft_id)},
        {"$set": {"filename": fname, "previewUrl": f"{settings.BASE_URL}/uploads/{fname}"}},
        return_document=True,
    )
    return Draft(**_serialize(doc))

# --- ÚJ: SDXL AI photo a drafthoz (olcsó TEST mód) ---
@router.post("/drafts/{draft_id}/ai_photo", response_model=Draft)
async def ai_photo(draft_id: str):
    d = db.drafts.find_one({"_id": ObjectId(draft_id)})
    if not d:
        raise HTTPException(404, "Draft not found")

    persona = _load_persona_or_404(d.get("personaId"))
    from app.services.ai_image import build_prompt, generate_sdxl
    title = d.get("title","").strip()
    # trend tag-eket vegyük a draft hashtags-ből, ha van
    trend_tags = d.get("hashtags") or []

    positive, negative = build_prompt(
        persona_name=persona.get("name"),
        topic=title or "lifestyle post",
        trend_tags=trend_tags
    )

    # SDXL txt2img (olcsó)
    _, url = await generate_sdxl(positive, negative_prompt=negative, width=896, height=1152, steps=26, guidance=7.0)

    # previewUrl frissítése (filename-t nem kötelező eltárolni, mert az URL tartós)
    doc = db.drafts.find_one_and_update(
        {"_id": ObjectId(draft_id)},
        {"$set": {"previewUrl": url}},
        return_document=True,
    )
    return Draft(**_serialize(doc))

# --- igazából nem kell az export zip---
@router.get("/drafts/{draft_id}/export")
def export_draft_zip(draft_id: str):
    d = db.drafts.find_one({"_id": ObjectId(draft_id)})
    if not d:
        raise HTTPException(404, "Draft not found")

    mem = BytesIO()
    with ZipFile(mem, "w") as z:
        caption_text = (d.get("caption") or "").strip()
        tags = d.get("hashtags", [])
        if tags:
            caption_text += ("\n\n" + " ".join("#"+t for t in tags))
        z.writestr("caption.txt", caption_text or "Add your caption here")

        fname = d.get("filename")
        if fname:
            path = os.path.join(UPLOAD_DIR, fname)
            if os.path.exists(path):
                with open(path, "rb") as f:
                    z.writestr("image.jpg", f.read())

        meta = (
            '{\n'
            f'  "title": "{d.get("title","")}",\n'
            f'  "category": "{d.get("category","")}",\n'
            f'  "status": "{d.get("status","draft")}"\n'
            '}'
        )
        z.writestr("meta.json", meta)

    mem.seek(0)
    return StreamingResponse(
        mem, media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="manual_post_kit_{draft_id}.zip"'}
    )

