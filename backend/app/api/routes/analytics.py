from typing import List
from datetime import datetime, timedelta
from bson import ObjectId
from fastapi import APIRouter

from app.core.db import db

router = APIRouter()

def _last_days(n: int = 7):
    today = datetime.utcnow().date()
    return [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(n-1, -1, -1)]

@router.get("/analytics")
def analytics():
    CATS = ["workout", "meal", "lifestyle"]
    STAT = ["draft", "approved"]

    by_cat_raw = list(db.drafts.aggregate([
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$project": {"category": "$_id", "_id": 0, "count": 1}}
    ]))
    by_cat_map = {x["category"]: x["count"] for x in by_cat_raw}
    by_cat = [{"category": c, "count": by_cat_map.get(c, 0)} for c in CATS]

    by_status_raw = list(db.drafts.aggregate([
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        {"$project": {"status": "$_id", "_id": 0, "count": 1}}
    ]))
    by_status_map = {x["status"]: x["count"] for x in by_status_raw}
    by_status = [{"status": s, "count": by_status_map.get(s, 0)} for s in STAT]

    day_keys = _last_days(7)
    per_day_map = {k: 0 for k in day_keys}
    since = datetime.utcnow() - timedelta(days=6)
    per_day_raw = list(db.drafts.aggregate([
        {"$match": {"_id": {"$gte": ObjectId.from_datetime(since)}}},
        {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": {"$toDate": "$_id"}}}, "count": {"$sum": 1}}},
        {"$project": {"day": "$_id", "_id": 0, "count": 1}}
    ]))
    for row in per_day_raw:
        if row["day"] in per_day_map:
            per_day_map[row["day"]] = row["count"]
    per_day = [{"day": k, "count": per_day_map[k]} for k in day_keys]

    total = sum(x["count"] for x in by_cat)
    return {"total": total, "byCategory": by_cat, "byStatus": by_status, "perDay": per_day}
