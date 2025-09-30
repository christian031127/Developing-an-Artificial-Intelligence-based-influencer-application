from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Query
from app.core.settings import settings
from app.services.trends import get_trends, _DEFAULT_SEED

router = APIRouter()

@router.get("/trends")
def trends(
    geo: str = Query(default=settings.TRENDS_GEO),
    window: str = Query(default=settings.TRENDS_WINDOW, pattern="^(7d|30d|90d)$"),
    seed: Optional[str] = Query(default=None, description="Comma-separated seed terms")
):
    seed_terms = [s.strip() for s in (seed.split(",") if seed else _DEFAULT_SEED) if s.strip()]
    try:
        return get_trends(geo=geo, window=window, seed=seed_terms)
    except Exception:
        # graceful fallback
        return {
            "geo": geo,
            "window": window,
            "keywords": seed_terms[:20],
            "fetchedAt": datetime.utcnow().isoformat() + "Z",
            "note": "fallback: pytrends unavailable",
        }
