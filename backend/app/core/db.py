# Simple Mongo client. Use one per process.
from pymongo import MongoClient, ASCENDING
from app.core.settings import settings

client = MongoClient(settings.MONGO_URI)
db = client[settings.MONGO_DB]

# Ensure TTL index for trends cache (expires after TRENDS_TTL_SECONDS)
try:
    db.trends_cache.create_index(
        [("cacheKey", ASCENDING)], name="cache_key_idx", unique=True
    )
    db.trends_cache.create_index(
        [("createdAt", ASCENDING)],
        name="trends_ttl_idx",
        expireAfterSeconds=settings.TRENDS_TTL_SECONDS,
    )
except Exception:
    # don’t crash on startup if already exists
    pass
