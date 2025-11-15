from __future__ import annotations
from typing import List, Dict
from datetime import datetime, timezone
import hashlib
from pytrends.request import TrendReq
from app.core.db import db
from app.core.settings import settings

# pytrends 'pn' mapping a napi trending searches híváshoz
_PN_MAP = {
    "HU": "hungary",
    "US": "united_states",
    "GB": "united_kingdom",
    "DE": "germany",
    "FR": "france",
    "ES": "spain",
    "IT": "italy",
    "PT": "portugal",
    "PL": "poland",
    "RO": "romania",
    "SK": "slovakia",
    "CZ": "czech_republic",
}

def _pn_for_geo(geo: str) -> str:
    return _PN_MAP.get((geo or "").upper(), "united_states")

def _cache_key(geo: str, window: str) -> str:
    raw = f"{geo}|{window}|TRENDING_ONLY"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()

_DEFAULT_SEED = [
    # general & education
    "AI tools for students",
    "thesis writing tips",
    "time management",
    "note-taking apps",
    "study motivation",
    # technology & economy
    "latest AI trends",
    "blockchain news",
    "startup ideas",
    "green tech",
    "digital marketing",
    # travel & culture
    "budget travel",
    "hidden gems Europe",
    "remote work lifestyle",
    "coffee culture",
    "local food experiences",
    # society & career
    "mental health awareness",
    "sustainable fashion",
    "personal branding",
    "career change",
    "work-life balance",
]

def _last_cached_keywords() -> List[str]:
    """Utolsó mentett kulcsszavak a Mongo cache-ből."""
    doc = db.trends_cache.find_one(sort=[("createdAt", -1)])
    if doc and isinstance(doc.get("payload"), dict):
        arr = doc["payload"].get("keywords") or []
        if isinstance(arr, list) and arr:
            return [str(x) for x in arr][:25]
    return []

def _today_trending_keywords(geo: str, limit: int = 25) -> List[str]:
    """Napi 'trending searches' az adott országra."""
    py = TrendReq(hl="en-US", tz=0)
    pn = _pn_for_geo(geo)
    try:
        df = py.trending_searches(pn=pn)
        kws = [str(x).strip() for x in df.iloc[:, 0].tolist() if str(x).strip()]
        return kws[:limit]
    except Exception:
        return []

def fetch_trends_from_google(geo: str, window: str) -> Dict:
    keywords = _today_trending_keywords(geo=geo, limit=25)
    if not keywords:
        keywords = _last_cached_keywords() or _DEFAULT_SEED

    # ÚJ: deduplikálás + vágás + végső garancia
    seen = set()
    keywords = [clean for orig in keywords if (clean := str(orig).strip()) and (clean.lower() not in seen and not seen.add(clean.lower()))]
    if not keywords:
        keywords = _DEFAULT_SEED[:]

    return {
        "geo": geo,
        "window": window,
        "keywords": keywords[:25],
        "fetchedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mode": "today_trending",
    }


def get_trends(geo: str, window: str) -> Dict:
    """Cache-first (Mongo TTL). Ha nincs adat, újrafetch."""
    key = _cache_key(geo, window)
    doc = db.trends_cache.find_one({"cacheKey": key})
    if doc and isinstance(doc.get("payload"), dict):
        return doc["payload"]

    payload = fetch_trends_from_google(geo=geo, window=window)
    db.trends_cache.update_one(
        {"cacheKey": key},
        {"$set": {"payload": payload, "createdAt": datetime.now(timezone.utc)}},
        upsert=True,
    )
    return payload
