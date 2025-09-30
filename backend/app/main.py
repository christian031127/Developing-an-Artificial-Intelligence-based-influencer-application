from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.files import UPLOAD_DIR  # biztosítja, hogy a /app/uploads létezik

# Routers
from app.api.routes.health import router as health_router
from app.api.routes.personas import router as personas_router
from app.api.routes.drafts import router as drafts_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.trends import router as trends_router
from app.api.routes.characters import router as characters_router

app = FastAPI(title="AI Influencer API")

# CORS (FE dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static uploads
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# API
app.include_router(health_router, prefix="/api")
app.include_router(personas_router, prefix="/api", tags=["personas"])
app.include_router(drafts_router, prefix="/api", tags=["drafts"])
app.include_router(analytics_router, prefix="/api", tags=["analytics"])
app.include_router(trends_router, prefix="/api", tags=["trends"])
app.include_router(characters_router, prefix="/api", tags=["characters"])
