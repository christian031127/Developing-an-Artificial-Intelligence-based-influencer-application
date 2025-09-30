import os
from uuid import uuid4
from fastapi import UploadFile, HTTPException

# Folders
UPLOAD_DIR = "/app/uploads"
CHAR_DIR = os.path.join(UPLOAD_DIR, "characters")

# Ensure dirs exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHAR_DIR, exist_ok=True)

# Allowed image types
ALLOWED_IMG = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

def save_upload(file: UploadFile, folder: str) -> tuple[str, str]:
    """
    Save UploadFile to disk, return (filename, abs_path).
    """
    ext = ALLOWED_IMG.get(file.content_type)
    if not ext:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    fname = f"{uuid4()}{ext}"
    abs_path = os.path.join(folder, fname)

    with open(abs_path, "wb") as out:
        out.write(file.file.read())

    return fname, abs_path
