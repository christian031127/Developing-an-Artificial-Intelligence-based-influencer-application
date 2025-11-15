from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
import os
from bson import ObjectId

from app.core.db import db
from app.core.settings import settings
from app.core.files import CHAR_DIR, save_upload

router = APIRouter(tags=["personas"])

class PersonaOut(BaseModel):
    id: str
    name: str
    ref_image_url: Optional[str] = None   # referencia portré URL
    identity_hint: Optional[str] = None   # pl. "female, 30s"
    style: str = "photo_realistic"        # megjelenési stílus
    mood: str = "neutral"                 # arckifejezés / hangulat
    bg: str = "studio_gray"               # háttér típusa

# --- DB -> API serializálás (régi mezők nélkül) ---
def _s(doc: dict) -> PersonaOut:
    return PersonaOut(
        id=str(doc["_id"]),
        name=doc.get("name", ""),
        ref_image_url=doc.get("ref_image_url"),
        identity_hint=doc.get("identity_hint"),
        style=doc.get("style", "photo_realistic"),
        mood=doc.get("mood", "neutral"),
        bg=doc.get("bg", "studio_gray"),
    )

@router.get("/personas", response_model=list[PersonaOut])
def list_personas():
    """Az összes persona lekérdezése (legújabb elöl)."""
    return [_s(d) for d in db.personas.find().sort("_id", -1)]

@router.post("/personas", response_model=PersonaOut)
async def create_persona(
    # ⚠ Kötelező kép feltöltés — URL LE VAN TILTVA
    file: UploadFile = File(...),
    # Alap metaadatok
    name: str = Form(...),
    identity_hint: Optional[str] = Form(None),
    style: str = Form("photo_realistic"),
    mood: str = Form("neutral"),
    bg: str = Form("studio_gray"),
):
    """
    Új persona létrehozása KIZÁRÓLAG képfeltöltéssel.
    - A fájlt eltároljuk /uploads/characters alá (filename)
    - A kiszolgált URL-t (ref_image_url) visszaadjuk a kliensnek
    """
    # 1) Kép mentése
    fname, _ = save_upload(file, CHAR_DIR)
    url = f"{settings.BASE_URL}/uploads/characters/{fname}"

    # 2) DB dokumentum
    doc = {
        "name": name.strip(),
        "ref_image_url": url,
        "filename": fname,              # <- fontos: törléshez és init_path feloldáshoz
        "identity_hint": identity_hint,
        "style": style,
        "mood": mood,
        "bg": bg,
    }
    res = db.personas.insert_one(doc)
    doc["_id"] = res.inserted_id
    return _s(doc)

@router.patch("/personas/{persona_id}", response_model=PersonaOut)
def update_persona(persona_id: str, body: dict):
    """
    Persona mezőinek frissítése (csak szöveges/vizuális meta).
    Képet itt NEM lehet cserélni (újra létrehozással vagy külön képcsere-endpointtal kezelhető).
    """
    allowed = {"name", "identity_hint", "style", "mood", "bg"}
    update = {k: v for k, v in (body or {}).items() if k in allowed}
    if not update:
        raise HTTPException(400, "Nincs módosítható mező.")

    doc = db.personas.find_one_and_update(
        {"_id": ObjectId(persona_id)},
        {"$set": update},
        return_document=True,
    )
    if not doc:
        raise HTTPException(404, "Persona nem található.")
    return _s(doc)

@router.delete("/personas/{persona_id}")
def delete_persona(persona_id: str):
    """
    Persona törlése. Ha a képet mi mentettük ('filename'), töröljük a fájlt is.
    """
    doc = db.personas.find_one({"_id": ObjectId(persona_id)})
    if not doc:
        raise HTTPException(404, "Persona nem található.")

    if (fn := doc.get("filename")):
        p = os.path.join(CHAR_DIR, fn)
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass

    db.personas.delete_one({"_id": ObjectId(persona_id)})
    return {"ok": True}
