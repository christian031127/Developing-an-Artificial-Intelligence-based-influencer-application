# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# API routers
from app.api.routes.health import router as health_router
from app.api.routes.personas_db import router as personas_db_router
from app.api.routes.drafts import router as drafts_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.trends import router as trends_router
from app.api.routes.characters import router as characters_router
from app.api.routes import images as images_router  # POST /api/images/generate

app = FastAPI(title="AI Influencer API")

# === Statikus könyvtárak beállítása (ABSZOLÚT utak) ===
# A konténerben a kód /app alatt van:
UPLOADS_ROOT = Path("/app/uploads").resolve()
IMAGES_DIR = (UPLOADS_ROOT / "images").resolve()
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# A TELJES uploads mappát szolgáljuk ki:
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_ROOT)), name="uploads")

# === Egyszerű root + debug ===
@app.get("/")
def root():
    return {
        "ok": True,
        "uploads_root": str(UPLOADS_ROOT),
        "images_dir": str(IMAGES_DIR),
    }

@app.get("/__debug_list")
def __debug_list():
    files = [p.name for p in IMAGES_DIR.glob("*.jpg")]
    return {"count": len(files), "images": files[:50]}

# === CORS + API route-ok ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(drafts_router, prefix="/api", tags=["drafts"])
app.include_router(analytics_router, prefix="/api", tags=["analytics"])
app.include_router(trends_router, prefix="/api", tags=["trends"])
app.include_router(characters_router, prefix="/api", tags=["characters"])
app.include_router(personas_db_router, prefix="/api")
app.include_router(images_router.router)  # /api/images/generate
