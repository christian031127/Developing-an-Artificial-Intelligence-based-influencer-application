from typing import List
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from fastapi import APIRouter

from app.core.db import db

router = APIRouter()


def _last_days(n: int = 7):
    today = datetime.now(timezone.utc).date()
    return [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(n - 1, -1, -1)]


@router.get("/analytics")
def analytics():
    # --- BY CATEGORY: dinamikusan, a draftokból kiolvasva ---
    # ha nincs category mező, "uncategorized" néven jelenik meg
    by_cat = list(
        db.drafts.aggregate(
            [
                {
                    "$group": {
                        "_id": {"$ifNull": ["$category", "uncategorized"]},
                        "count": {"$sum": 1},
                    }
                },
                {"$project": {"category": "$_id", "_id": 0, "count": 1}},
                {"$sort": {"count": -1, "category": 1}},
            ]
        )
    )

    # --- BY STATUS: draft / approved (plusz bármi egyéb, ha lenne) ---
    by_status = list(
        db.drafts.aggregate(
            [
                {
                    "$group": {
                        "_id": {"$ifNull": ["$status", "draft"]},
                        "count": {"$sum": 1},
                    }
                },
                {"$project": {"status": "$_id", "_id": 0, "count": 1}},
                {"$sort": {"status": 1}},
            ]
        )
    )

    # --- PER DAY (utolsó 7 nap) ---
    day_keys = _last_days(7)
    per_day_map = dict.fromkeys(day_keys, 0)
    since = (datetime.now(timezone.utc) - timedelta(days=6)).replace(tzinfo=None)

    per_day_raw = list(
        db.drafts.aggregate(
            [
                {"$match": {"_id": {"$gte": ObjectId.from_datetime(since)}}},
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": {"$toDate": "$_id"},
                            }
                        },
                        "count": {"$sum": 1},
                    }
                },
                {"$project": {"day": "$_id", "_id": 0, "count": 1}},
            ]
        )
    )
    for row in per_day_raw:
        if row["day"] in per_day_map:
            per_day_map[row["day"]] = row["count"]
    per_day = [{"day": k, "count": per_day_map[k]} for k in day_keys]

    # Összes draft száma – minden státuszra
    total = sum(x["count"] for x in by_status)

    return {
        "total": total,
        "byCategory": by_cat,
        "byStatus": by_status,
        "perDay": per_day,
    }
