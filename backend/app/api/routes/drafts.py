import os, random
from io import BytesIO
from zipfile import ZipFile
from uuid import uuid4
from typing import List, Optional, Literal
from datetime import datetime, timedelta
from urllib.parse import urlparse
from random import randint

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from bson import ObjectId

from app.core.settings import settings
from app.core.db import db
from app.core.files import UPLOAD_DIR

from app.services.ai_text import gen_caption_and_tags, guess_category
from app.services.ai_image import generate_openai_img2img, build_image_prompt_from_persona

router = APIRouter(tags=["drafts"])

# --- Kategória-következtetés egyszerűen
# --- Kategória-következtetés (10-es lista, semleges) -------------------------
CATEGORY_KEYWORDS = {
    "education":    {"study","thesis","exam","learn","university","school","notes"},
    "technology":   {"artificial intelligence","blockchain","tech","app","software","code","coding","python","react","docker","api"},
    "finance":      {"etf","dividend","budget","invest","stock","crypto","bitcoin","btc","usd","saving"},
    "health":       {"mental health","mindfulness","wellbeing","sleep"},
    "fitness":      {"workout","leg day","glute","hypertrophy","gym","hiit","mobility","strength","run","yoga"},
    "travel":       {"trip","travel","porto","lisbon","beach","flight","hotel","brunch"},
    "food":         {"recipe","meal","food","coffee","snack","breakfast","cook"},
    "lifestyle":    {"routine","morning","minimalism","design","home","decor","style"},
    "career":       {"job","career","interview","cv","portfolio","work"},
    "productivity": {"time","productivity","focus","routine","tasks","schedule"},
}


class Idea(BaseModel):
    id: str
    title: str
    category: Literal[
        "education","technology","finance","health","fitness",
        "travel","food","lifestyle","career","productivity"
    ]

class DraftCreate(BaseModel):
    ideaId: Optional[str] = None
    title: str
    category: Literal[
        "education","technology","finance","health","fitness",
        "travel","food","lifestyle","career","productivity"
    ] = "lifestyle"
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

def infer_category(doc: dict) -> str:
    hay = " ".join([
        str(doc.get("title") or ""),
        str(doc.get("caption") or ""),
        " ".join(doc.get("hashtags") or []),
    ]).lower()

    hay = hay.replace("ai_generated", "").replace(" ai ", " ")
    
    best = ("lifestyle", 0)
    for cat, kws in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in kws if kw in hay)
        if score > best[1]:
            best = (cat, score)
    return best[0]

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
    """Persona betöltése vagy 400 (rossz ID / nem létezik)."""
    try:
        p = db.personas.find_one({"_id": ObjectId(persona_id)})
    except Exception:
        p = None
    if not p:
        raise HTTPException(400, "personaId is invalid or not found")
    return p

def _resolve_init_path_from_persona(p: dict) -> str | None:
    """
    Persona portré → lokális útvonal feloldása.
    - Előny: feltöltött filename
    - Alternatíva: ref_image_url (ha /uploads/...-ra mutat)
    """
    if p.get("filename"):
        return f"/app/uploads/characters/{p['filename']}"
    if p.get("ref_image_url"):
        parsed = urlparse(p["ref_image_url"])
        if parsed.path.startswith("/uploads/"):
            return "/app" + parsed.path
    return None

@router.post("/drafts", response_model=Draft)
async def create_draft(body: DraftCreate):
    persona = _load_persona_or_404(body.personaId)

    # 1) Caption + hashtags (AI → fallback); NINCS több brand_tag
    caption = (body.caption or "").strip()
    hashtags = list(body.hashtags or [])
    if not caption or not hashtags:
        try:
            cap, tags = await gen_caption_and_tags(
                topic=body.title,
                category=body.category,
                custom_text=body.customText or "friendly, concise",
            )
            caption = caption or cap
            hashtags = hashtags or tags  # gen_caption_and_tags már hozzáadja az 'ai_generated'-et
        except Exception:
            caption = caption or "Quick tip inside."
            hashtags = hashtags or ["daily","ideas","trending","ai_generated"]
            
    # garantáljuk az ai_generated taget
    if "ai_generated" not in [h.lower() for h in (hashtags or [])]:
        hashtags.append("ai_generated")

    # 2) Kategória következtetése a most elkészült adatokból, és MENTJÜK is a draftba
    draft_probe = {"title": body.title, "caption": caption, "hashtags": hashtags, "category": body.category}
    category = infer_category(draft_probe)

    # 3) Persona portré → init_path (img2img-hez kötelező)
    init_path = _resolve_init_path_from_persona(persona)
    if not init_path:
        raise HTTPException(400, "Persona portrait not found; cannot run img2img.")

    # 4) Prompt (persona + topic + trendTags≈hashtags)
    positive, _ = build_image_prompt_from_persona(
        persona,
        topic=body.title,
        trend_tags=hashtags
    )

    # 5) OpenAI img2img
    _, url = await generate_openai_img2img(
        init_image_path=init_path,
        prompt=positive,
        size="1024x1024",
        pad_to_portrait=True,
    )

    # 6) Mentés – KATEGÓRIÁVAL együtt
    doc = body.model_dump()
    doc.update({
        "caption": caption,
        "hashtags": hashtags,
        "status": "draft",
        "previewUrl": url,
        "category": category,   # <-- itt kerül be
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

    category = infer_category(doc)
    persona_hint = doc.get("personaId") or ""
    metrics = _simulate_metrics(category, persona_hint)

    exists = db.feed_posts.find_one({"draftId": str(doc["_id"])})
    if not exists:
        db.feed_posts.insert_one({
            "draftId": str(doc["_id"]),
            "title": doc.get("title"),
            "caption": doc.get("caption"),
            "hashtags": doc.get("hashtags", []),
            "imageUrl": doc.get("previewUrl"),
            "personaId": persona_hint,
            "category": category,
            "publishedAt": datetime.utcnow(),
            "metrics": metrics,   # csak a 4 KPI lesz benne
        })

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

    try:
        cap, tags = await gen_caption_and_tags(
            topic=d.get("title",""),
            category=d.get("category","lifestyle"),
            custom_text=d.get("customText") or "friendly, concise",
        )
    except Exception:
        cap = (d.get("title") or "New post") + " — save it!"
        tags = d.get("hashtags") or ["ai_generated"]

    if "ai_generated" not in [h.lower() for h in (tags or [])]:
        tags.append("ai_generated")

    # új kategória a friss szöveg/hashtag alapján
    new_probe = {"title": d.get("title",""), "caption": cap, "hashtags": tags, "category": d.get("category","lifestyle")}
    category = infer_category(new_probe)

    doc = db.drafts.find_one_and_update(
        {"_id": ObjectId(draft_id)},
        {"$set": {"caption": cap, "hashtags": tags, "category": category}},
        return_document=True
    )
    return Draft(**_serialize(doc))

# A régi regen_image / ai_photo endpointok érintetlenek maradnak; nem hívódnak, így nem zavarják a működést.

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

def _simulate_metrics(category: str, persona_hint: str = "") -> dict:
    cat_base = {
    "fitness": (1800, 4800),
    "food": (1200, 3500),
    "lifestyle": (900, 3000),
    "finance": (800, 2500),
    "travel": (1500, 4200),
    "technology": (1000, 3200),
    "education": (900, 2800),
    "career": (900, 2600),
    "productivity": (1100, 3200),
    "health": (950, 3000),
}.get((category or "lifestyle").lower(), (900, 2800))


    reach = random.randint(*cat_base)
    impressions = int(reach * random.uniform(1.2, 1.6))

    bias = 1.0
    p = (persona_hint or "").lower()
    if any(k in p for k in ["coach","fit","gym"]): bias = 1.15
    elif any(k in p for k in ["food","chef"]):     bias = 1.25
    elif any(k in p for k in ["crypto","fin"]):    bias = 0.90

    like_rate = random.uniform(0.02, 0.06) * bias
    comment_rate = random.uniform(0.002, 0.015)
    # save/share most nem kell, mert a panelen nem mutatjuk
    likes = int(reach * like_rate)
    comments = int(reach * comment_rate)

    return {
        "impressions": impressions,
        "reach": reach,
        "likes": likes,
        "comments": comments,
    }

@router.get("/feed")
def list_feed_posts():
    """Lista a feedben lévő posztokról (legújabb elöl)."""
    posts = []
    for p in db.feed_posts.find().sort("publishedAt", -1):
        p["id"] = str(p.pop("_id"))  # kliensnek szebb string ID
        posts.append(p)
    return {"items": posts}


@router.delete("/feed/{post_id}")
def delete_feed_post(post_id: str):
    """Feed poszt törlése (csak a szimulált feedből)."""
    try:
        oid = ObjectId(post_id)
    except Exception:
        raise HTTPException(400, "Invalid post id")

    res = db.feed_posts.delete_one({"_id": oid})
    if not res.deleted_count:
        raise HTTPException(404, "Feed post not found")
    return {"ok": True}
