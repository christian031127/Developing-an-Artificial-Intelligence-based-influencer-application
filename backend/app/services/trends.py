from __future__ import annotations
from typing import List, Dict, Tuple
from datetime import datetime
import hashlib
from pytrends.request import TrendReq
from app.core.db import db
from app.core.settings import settings

_TIMEFRAME_MAP = {
    "7d": "now 7-d",
    "30d": "today 1-m",
    "90d": "today 3-m",
}

_DEFAULT_SEED = [
    "leg day","glute workout","protein breakfast","meal prep","active rest",
    "hypertrophy","budgeting","ETF","dividends","morning routine","productivity",
    "deep work","HIIT","mobility","macro tracking","study hacks","minimalism",
    "home workout","healthy snacks","strength training"
]

def _cache_key(geo: str, window: str, seed: List[str]) -> str:
    raw = f"{geo}|{window}|{'|'.join(seed)}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()

def _select_top_unique(candidates: List[Tuple[str,int]], limit: int=20) -> List[str]:
    seen, out = set(), []
    for kw, score in sorted(candidates, key=lambda x: x[1], reverse=True):
        k = kw.strip().lower()
        if k and k not in seen:
            seen.add(k)
            out.append(kw)
        if len(out) >= limit:
            break
    return out

def _timeframe(window: str) -> str:
    return _TIMEFRAME_MAP.get(window, _TIMEFRAME_MAP[settings.TRENDS_WINDOW])

def fetch_trends_from_google(geo: str, window: str, seed: List[str]) -> Dict:
    """
    Pull 'rising' related queries for each seed keyword, dedupe, rank by score.
    Returns { geo, window, keywords: [..], fetchedAt }
    """
    tf = _timeframe(window)
    py = TrendReq(hl="en-US", tz=0)
    candidates: List[Tuple[str,int]] = []

    # Pull related rising queries per seed
    for term in seed:
        try:
            py.build_payload([term], timeframe=tf, geo=geo)
            rq = py.related_queries()
            # {'term': {'top': df, 'rising': df}}
            if term in rq and rq[term] and rq[term].get("rising") is not None:
                df = rq[term]["rising"]
                # df columns: 'query','value'
                for row in df.itertuples(index=False):
                    q = str(row.query)
                    v = int(getattr(row, "value", 50))
                    candidates.append((q, v))
        except Exception:
            # swallow term-level errors (rate limits, etc.)
            continue

    keywords = _select_top_unique(candidates, limit=20)
    return {
        "geo": geo,
        "window": window,
        "keywords": keywords,
        "fetchedAt": datetime.utcnow().isoformat() + "Z",
    }

def get_trends(geo: str, window: str, seed: List[str]) -> Dict:
    """
    Cache-first (Mongo TTL). Cache key = sha1(geo|window|seed).
    """
    key = _cache_key(geo, window, seed)
    doc = db.trends_cache.find_one({"cacheKey": key})
    if doc and isinstance(doc.get("payload"), dict):
        return doc["payload"]

    payload = fetch_trends_from_google(geo=geo, window=window, seed=seed)
    db.trends_cache.update_one(
        {"cacheKey": key},
        {"$set": {"payload": payload, "createdAt": datetime.utcnow()}},
        upsert=True,
    )
    return payload
