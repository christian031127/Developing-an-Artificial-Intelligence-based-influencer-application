from fastapi import APIRouter, HTTPException
from datetime import datetime
from bson import ObjectId
from app.core.db import db
from app.services.ai_text import generate_agent_critique
from typing import Dict, Any

from urllib.parse import urlparse

from app.services.ai_image import (
    generate_openai_img2img,
    build_image_prompt_from_persona,
)


router = APIRouter(prefix="/api/agent", tags=["agent"])

def _generate_image(prompt: str) -> str:
    try:
        from app.services.ai_image import generate_image as _impl
    except Exception:
        try:
            from app.services.ai_image import generate as _impl
        except Exception:
            from app.services.ai_image import create_image as _impl
    return _impl(prompt)

def _resolve_init_path_from_persona(p: dict | None) -> str | None:
    """
    Persona portrait → local file path for img2img.
    - First try uploaded filename
    - Then ref_image_url if it points into /uploads/…
    """
    if not p:
        return None
    if p.get("filename"):
        return f"/app/uploads/characters/{p['filename']}"
    if p.get("ref_image_url"):
        parsed = urlparse(p["ref_image_url"])
        if parsed.path.startswith("/uploads/"):
            return "/app" + parsed.path
    return None

# ---- KPI segéd
def _kpis(m: dict) -> dict:
    reach = max(1, int(m.get("reach") or 0))
    likes = int(m.get("likes") or 0)
    comments = int(m.get("comments") or 0)
    impressions = int(m.get("impressions") or 0)

    like_rate = likes / reach
    comment_rate = comments / reach
    # engagement rate itt a két mutató (kérésed szerint csak 4 KPI-t tartunk)
    eng_rate = (likes + comments) / reach

    # egyszerű score (arány alapú, 0..100)
    like_norm = min(like_rate, 0.08) / 0.08
    comm_norm = min(comment_rate, 0.02) / 0.02
    score = round(100 * (0.65 * like_norm + 0.35 * comm_norm))

    return {
        "reach": reach,
        "impressions": impressions,
        "likes": likes,
        "comments": comments,
        "likeRate": round(like_rate, 4),
        "commentRate": round(comment_rate, 4),
        "engagementRate": round(eng_rate, 4),
        "score": score,
    }

# ---- /critique: LLM készít személyre szabott tippeket + image intents
@router.post("/critique/{post_id}")
def critique_post(post_id: str):
    try:
        oid = ObjectId(post_id)
    except Exception:
        raise HTTPException(400, "Invalid post id")

    post = db.feed_posts.find_one({"_id": oid})
    if not post:
        raise HTTPException(404, "Post not found")

    k = _kpis(post.get("metrics") or {})
    payload = {
        "title": post.get("title") or "",
        "caption": post.get("caption") or "",
        "hashtags": post.get("hashtags") or [],
        "category": post.get("category") or "lifestyle",
        "personaId": post.get("personaId") or "",
        "kpis": k,
    }

    # LLM-ből strukturált válasz (nem if-else)
    agent = generate_agent_critique(payload)

    # kiegészítjük fix mezőkkel és mentjük
    agent_record: Dict[str, Any] = {
        "score": k["score"],
        "kpis": {"likeRate": k["likeRate"], "commentRate": k["commentRate"], "engagementRate": k["engagementRate"]},
        "insights": agent.get("insights", []),
        "recommendations": agent.get("recommendations", []),
        "nextDraftConfig": agent.get("nextDraftConfig", {}),
        "version": "v2",
        "createdAt": datetime.utcnow().isoformat(),
    }
    db.feed_posts.update_one({"_id": oid}, {"$set": {"agent": agent_record}})
    return agent_record

# ---- /apply: létrehoz egy új draftot és képet generál az intents alapján
@router.post("/apply/{post_id}")
async def apply_recommendations(post_id: str):
    # 1) Feed post betöltése
    try:
        oid = ObjectId(post_id)
    except Exception:
        raise HTTPException(400, "Invalid post id")

    post = db.feed_posts.find_one({"_id": oid})
    if not post:
        raise HTTPException(404, "Post not found")

    agent = post.get("agent") or {}
    cfg = (agent.get("nextDraftConfig") or {}).copy()

    # 2) Szöveges változások az LLM-től (ha adott)
    new_caption = cfg.pop("caption", None) or (post.get("caption") or "")
    new_hashtags = cfg.pop("hashtags", None) or (post.get("hashtags") or [])[:3]

    # 3) Kép-intents az LLM-től
    intent = cfg.pop("image", {}) or {}
    style = intent.get("style", "clean minimal")
    framing = intent.get("framing", "medium shot")
    lighting = intent.get("lighting", "soft daylight")
    background = intent.get("background", "café interior")
    overlay = intent.get("textOverlay", "none")

    # 4) Persona + topic alap prompt (ugyanúgy, mint draftnál)
    persona = None
    if post.get("personaId"):
        try:
            persona = db.personas.find_one({"_id": ObjectId(post["personaId"])})
        except Exception:
            persona = None

    base_positive, _ = build_image_prompt_from_persona(
        persona,
        topic=post.get("title") or "",
        trend_tags=new_hashtags,
    )

    # LLM-intents hozzáfűzése a prompt végére
    extra_bits = f"{style}, {framing}, {lighting}, {background} background"
    if overlay != "none":
        extra_bits += f", subtle text overlay: {overlay} (max 5 words)"

    prompt = f"{base_positive}, {extra_bits}"

    # 5) Persona portré → init image path
    init_path = _resolve_init_path_from_persona(persona)

    # 6) Új kép generálása OpenAI img2img-gel
    new_image_url = post.get("imageUrl")
    if init_path:
        try:
            _, new_image_url = await generate_openai_img2img(
                init_image_path=init_path,
                prompt=prompt,
                size="1024x1024",
                pad_to_portrait=True,
            )
        except Exception as e:
            # fallback: marad a régi kép
            print("agent.apply img2img error:", e)

    # 7) Új draft létrehozása
    draft_doc = {
        "title": post.get("title"),
        "category": post.get("category"),
        "caption": new_caption,
        "hashtags": new_hashtags,
        "personaId": post.get("personaId"),
        "previewUrl": new_image_url,
        "status": "draft",
        "createdAt": datetime.utcnow(),
    }
    ins = db.drafts.insert_one(draft_doc)
    draft_doc["id"] = str(ins.inserted_id)
    return draft_doc

