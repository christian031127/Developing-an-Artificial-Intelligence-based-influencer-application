from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Query
from app.core.settings import settings
from app.services.trends import get_trends

router = APIRouter()

@router.get("/trends")
def trends(
    geo: str = Query(default=settings.TRENDS_GEO),
    window: str = Query(default=settings.TRENDS_WINDOW, pattern="^(7d|30d|90d)$"),
    seed: Optional[str] = Query(default=None, description="(Ignored)"),
):
    """
    Mindig a napi országos trending searches-t adja vissza (max 25).
    A 'seed' paramétert figyelmen kívül hagyjuk.
    Válasz:
      { geo, window, keywords: [...], fetchedAt }
    """
    payload = get_trends(geo=geo, window=window)
    return {
        "geo": payload.get("geo", geo),
        "window": payload.get("window", window),
        "keywords": payload.get("keywords", [])[:25],
        "fetchedAt": payload.get("fetchedAt", datetime.utcnow().isoformat() + "Z"),
    }
