import os
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from bson import ObjectId

from app.core.db import db
from app.core.settings import settings
from app.core.files import CHAR_DIR, save_upload

router = APIRouter()

class Character(BaseModel):
    id: str
    name: str
    personaId: Optional[str] = None
    imageUrl: str
    filename: str
    createdAt: str

@router.get("/characters", response_model=List[Character])
def list_characters():
    docs = list(db.characters.find().sort("_id", -1))
    out = []
    for d in docs:
        out.append(Character(
            id=str(d["_id"]),
            name=d.get("name",""),
            personaId=d.get("personaId"),
            imageUrl=d.get("imageUrl",""),
            filename=d.get("filename",""),
            createdAt=d.get("createdAt",""),
        ))
    return out

@router.post("/characters", response_model=Character)
async def create_character(
    name: str = Form(...),
    personaId: Optional[str] = Form(default=None),
    file: UploadFile = File(...),
):
    fname, _ = save_upload(file, CHAR_DIR)
    url = f"{settings.BASE_URL}/uploads/characters/{fname}"
    doc = {
        "name": name.strip(),
        "personaId": personaId or None,
        "filename": fname,
        "imageUrl": url,
        "createdAt": datetime.utcnow().isoformat() + "Z",
    }
    res = db.characters.insert_one(doc)
    doc["_id"] = res.inserted_id
    return Character(
        id=str(res.inserted_id),
        name=doc["name"],
        personaId=doc["personaId"],
        imageUrl=doc["imageUrl"],
        filename=fname,
        createdAt=doc["createdAt"],
    )

@router.patch("/characters/{char_id}", response_model=Character)
def update_character(char_id: str, body: dict):
    allowed = {"name","personaId"}
    update = {k:v for k,v in (body or {}).items() if k in allowed}
    if not update:
        raise HTTPException(400, "No updatable fields provided")
    doc = db.characters.find_one_and_update(
        {"_id": ObjectId(char_id)}, {"$set": update}, return_document=True
    )
    if not doc:
        raise HTTPException(404, "Character not found")
    return Character(
        id=str(doc["_id"]),
        name=doc.get("name",""),
        personaId=doc.get("personaId"),
        imageUrl=doc.get("imageUrl",""),
        filename=doc.get("filename",""),
        createdAt=doc.get("createdAt",""),
    )

@router.delete("/characters/{char_id}")
def delete_character(char_id: str):
    doc = db.characters.find_one({"_id": ObjectId(char_id)})
    if not doc:
        raise HTTPException(404, "Character not found")
    if (fn := doc.get("filename")):
        p = os.path.join(CHAR_DIR, fn)
        if os.path.exists(p):
            try: os.remove(p)
            except: pass
    db.characters.delete_one({"_id": ObjectId(char_id)})
    return {"ok": True}
