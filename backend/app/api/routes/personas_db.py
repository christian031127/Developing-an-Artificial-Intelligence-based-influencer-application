from typing import List, Optional
from datetime import datetime
import os

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from bson import ObjectId

from app.core.db import db
from app.core.settings import settings
from app.core.files import CHAR_DIR, save_upload  # ugyanaz a mappa, jó a célra

router = APIRouter(tags=["personas"])

class PersonaOut(BaseModel):
    id: str
    name: str
    imageUrl: str
    filename: str
    brand_tag: Optional[str] = None
    watermark: Optional[str] = None
    tone: Optional[str] = None
    default_image_style: Optional[str] = None
    createdAt: str

def _s(doc: dict) -> PersonaOut:
    return PersonaOut(
        id=str(doc["_id"]),
        name=doc.get("name",""),
        imageUrl=doc.get("imageUrl",""),
        filename=doc.get("filename",""),
        brand_tag=doc.get("brand_tag"),
        watermark=doc.get("watermark"),
        tone=doc.get("tone"),
        default_image_style=doc.get("default_image_style"),
        createdAt=doc.get("createdAt",""),
    )

@router.get("/personas", response_model=List[PersonaOut])
def list_personas():
    return [_s(d) for d in db.personas.find().sort("_id", -1)]

@router.post("/personas", response_model=PersonaOut)
async def create_persona(
    name: str = Form(...),
    brand_tag: Optional[str] = Form(default=None),
    watermark: Optional[str] = Form(default=None),
    tone: Optional[str] = Form(default=None),
    default_image_style: Optional[str] = Form(default=None),
    file: UploadFile = File(...),
):
    fname, _ = save_upload(file, CHAR_DIR)
    url = f"{settings.BASE_URL}/uploads/characters/{fname}"

    doc = {
        "name": name.strip(),
        "filename": fname,
        "imageUrl": url,
        "brand_tag": (brand_tag or None),
        "watermark": (watermark or None),
        "tone": (tone or None),
        "default_image_style": (default_image_style or None),
        "createdAt": datetime.utcnow().isoformat() + "Z",
    }
    res = db.personas.insert_one(doc)
    doc["_id"] = res.inserted_id
    return _s(doc)

@router.patch("/personas/{persona_id}", response_model=PersonaOut)
def update_persona(persona_id: str, body: dict):
    allowed = {"name","brand_tag","watermark","tone","default_image_style"}
    update = {k:v for k,v in (body or {}).items() if k in allowed}
    if not update:
        raise HTTPException(400, "No updatable fields provided")

    doc = db.personas.find_one_and_update(
        {"_id": ObjectId(persona_id)},
        {"$set": update},
        return_document=True,
    )
    if not doc:
        raise HTTPException(404, "Persona not found")
    return _s(doc)

@router.delete("/personas/{persona_id}")
def delete_persona(persona_id: str):
    doc = db.personas.find_one({"_id": ObjectId(persona_id)})
    if not doc:
        raise HTTPException(404, "Persona not found")

    # töröljük a képfájlt is
    fn = doc.get("filename")
    if fn:
        p = os.path.join(CHAR_DIR, fn)
        if os.path.exists(p):
            try: os.remove(p)
            except: pass

    db.personas.delete_one({"_id": ObjectId(persona_id)})
    return {"ok": True}
