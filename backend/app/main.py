from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from bson import ObjectId
from uuid import uuid4
from io import BytesIO
from zipfile import ZipFile
import logging, os

from app.core.settings import settings
from app.core.db import db
from app.services.ai_text import gen_caption_and_tags
from app.services.imagegen import make_portrait
from app.services.trends import get_trends, _DEFAULT_SEED

logging.basicConfig(level=logging.INFO)

# ---------- App & CORS ----------
app = FastAPI(title="AI Influencer API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Static uploads ----------
UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ---------- Models ----------
class Idea(BaseModel):
    id: str
    title: str
    category: Literal["workout", "meal", "lifestyle"]

class DraftCreate(BaseModel):
    ideaId: Optional[str] = None
    title: str
    category: Literal["workout", "meal", "lifestyle"] = "workout"
    caption: str = ""
    hashtags: List[str] = Field(default_factory=list)
    style: Optional[str] = None  # future: image preset
    customText: Optional[str] = None  # LLM style hints

class Draft(DraftCreate):
    id: str
    status: Literal["draft", "approved"] = "draft"
    previewUrl: Optional[str] = None
    filename: Optional[str] = None

def _serialize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc

# ---------- Health ----------
@app.get("/api/healthz")
def healthz():
    return {"ok": True}

# ---------- Ideas (dummy for now) ----------
@app.get("/api/ideas", response_model=List[Idea])
def list_ideas():
    return [
        {"id": "i1", "title": "Leg day routine", "category": "workout"},
        {"id": "i2", "title": "High-protein breakfast bowl", "category": "meal"},
        {"id": "i3", "title": "Active rest day walk", "category": "lifestyle"},
    ]

# ---------- Drafts ----------
@app.get("/api/drafts", response_model=List[Draft])
def get_drafts():
    return [_serialize(d) for d in db.drafts.find().sort("_id", -1)]

@app.post("/api/drafts", response_model=Draft)
async def create_draft(body: DraftCreate):
    # (1) Caption + tags from LLM if not provided
    caption = (body.caption or "").strip()
    hashtags = list(body.hashtags or [])
    if not caption or not hashtags:
        try:
            cap, tags = await gen_caption_and_tags(topic=body.title, category=body.category, brand_tag="fitai")
            caption = caption or cap
            hashtags = hashtags or tags
        except Exception as e:
            logging.warning(f"caption-fallback: {e}")
            caption = caption or "Edzés inspo – mentsd el későbbre! 💪"
            hashtags = hashtags or ["fitai","gym","fitness","workout","lifestyle","training","inspo","fit","health","motivation"]

    # (2) Image: ALWAYS placeholder during dev (no external API cost)
    subtitle = "#" + (hashtags[0] if hashtags else "gym")
    img_bytes = make_portrait(title=body.title, subtitle=subtitle)
    fname = f"{uuid4()}.jpg"
    out_path = os.path.join(UPLOAD_DIR, fname)
    with open(out_path, "wb") as f:
        f.write(img_bytes)
    logging.info(f"[IMG] saved {fname} size={len(img_bytes)} -> {out_path}")

    # (3) Persist draft
    doc = body.model_dump()
    doc.update({
        "caption": caption,
        "hashtags": hashtags,
        "status": "draft",
        "filename": fname,
        "previewUrl": f"{settings.BASE_URL}/uploads/{fname}",
    })
    res = db.drafts.insert_one(doc)
    return Draft(id=str(res.inserted_id), **doc)

@app.post("/api/drafts/{draft_id}/approve", response_model=Draft)
def approve_draft(draft_id: str):
    res = db.drafts.find_one_and_update(
        {"_id": ObjectId(draft_id)},
        {"$set": {"status": "approved"}},
        return_document=True,
    )
    if not res:
        raise HTTPException(404, "Draft not found")
    return Draft(**_serialize(res))

@app.delete("/api/drafts/{draft_id}")
def delete_draft(draft_id: str):
    ok = db.drafts.delete_one({"_id": ObjectId(draft_id)}).deleted_count
    if not ok:
        raise HTTPException(404, "Draft not found")
    return {"ok": True}

# ---------- Manual Post Kit (ZIP) ----------
@app.get("/api/drafts/{draft_id}/export")
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
        mem,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="manual_post_kit_{draft_id}.zip"'}
    )

# ---------- Optional: caption regen (cheap) ----------
@app.post("/api/drafts/{draft_id}/regen_caption", response_model=Draft)
async def regen_caption(draft_id: str):
    d = db.drafts.find_one({"_id": ObjectId(draft_id)})
    if not d:
        raise HTTPException(404, "Draft not found")

    cap, tags = await gen_caption_and_tags(
        topic=d.get("title",""),
        category=d.get("category","workout"),
        brand_tag="fitai"
    )
    res = db.drafts.find_one_and_update(
        {"_id": ObjectId(draft_id)},
        {"$set": {"caption": cap, "hashtags": tags}},
        return_document=True,
    )
    return Draft(**_serialize(res))

# ---------- Analytics (MVP) ----------
from datetime import datetime, timedelta

@app.get("/api/analytics")
def analytics():
    """
    Returns simple content stats computed from drafts:
    - totals by category
    - totals by status
    - drafts created per day (last 7 days)
    """
    # by category
    by_cat = list(db.drafts.aggregate([
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$project": {"category": "$_id", "_id": 0, "count": 1}},
        {"$sort": {"category": 1}}
    ]))

    # by status
    by_status = list(db.drafts.aggregate([
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        {"$project": {"status": "$_id", "_id": 0, "count": 1}},
        {"$sort": {"status": 1}}
    ]))

    # per-day (last 7 days)
    since = datetime.utcnow() - timedelta(days=6)
    per_day = list(db.drafts.aggregate([
        {"$match": {"_id": {"$gte": ObjectId.from_datetime(since)}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": {"$toDate": "$_id"}}},
            "count": {"$sum": 1}
        }},
        {"$project": {"day": "$_id", "_id": 0, "count": 1}},
        {"$sort": {"day": 1}}
    ]))

    total = sum(x["count"] for x in by_cat) if by_cat else 0

    return {
        "total": total,
        "byCategory": by_cat,
        "byStatus": by_status,
        "perDay": per_day,
    }

# ---------- Trends ----------
@app.get("/api/trends")
def trends(
    geo: str = Query(default=settings.TRENDS_GEO),
    window: str = Query(default=settings.TRENDS_WINDOW, pattern="^(7d|30d|90d)$"),
    seed: Optional[str] = Query(default=None, description="Comma-separated seed terms")
):
    """
    Returns trending keywords for chips: { geo, window, keywords[], fetchedAt }
    Cache: 24h (Mongo TTL). Seed can be CSV; falls back to DEFAULT_SEED.
    """
    seed_terms = [s.strip() for s in (seed.split(",") if seed else _DEFAULT_SEED) if s.strip()]
    return get_trends(geo=geo, window=window, seed=seed_terms)

# ---------- Drafts ----------
@app.post("/api/drafts", response_model=Draft)
async def create_draft(body: DraftCreate):
    # 1) caption + tags via LLM (use customText if provided)
    caption = (body.caption or "").strip()
    hashtags = list(body.hashtags or [])
    if not caption or not hashtags:
        try:
            cap, tags = await gen_caption_and_tags(
                topic=body.title,
                category=body.category,
                brand_tag="fitai",
                custom_text=body.customText,   # NEW
            )
            caption = caption or cap
            hashtags = hashtags or tags
        except Exception as e:
            caption = caption or f"{body.title} — save it for later! 💪"
            hashtags = hashtags or ["fitai","gym","fitness","lifestyle","workout","inspo","fit","training","health","motivation"]

    # 2) image: placeholder (cost-free)
    subtitle = "#" + (hashtags[0] if hashtags else "fitai")
    img_bytes = make_portrait(title=body.title, subtitle=subtitle)
    fname = f"{uuid4()}.jpg"
    out_path = os.path.join(UPLOAD_DIR, fname)
    with open(out_path, "wb") as f:
        f.write(img_bytes)

    doc = body.model_dump()
    doc.update({
        "caption": caption,
        "hashtags": hashtags,
        "status": "draft",
        "filename": fname,
        "previewUrl": f"{settings.BASE_URL}/uploads/{fname}",
    })
    res = db.drafts.insert_one(doc)
    return Draft(id=str(res.inserted_id), **doc)
