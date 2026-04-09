"""
src/db/crud.py
──────────────
All database read/write operations (CRUD helpers).

Every module in the project imports from here — nothing talks to MongoDB directly
except this file and database.py. This makes it easy to test, mock, or swap DB later.
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo.collection import Collection
from pymongo.results import InsertOneResult, UpdateResult

from src.db.database import get_db

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _col(name: str) -> Collection:
    """Shorthand to get a collection from the active DB."""
    return get_db()[name]


def make_dedup_hash(source: str, title: str, timestamp: datetime | None) -> str:
    """
    Create a SHA256 hash used to detect duplicate raw events.
    Uses: source + first 60 chars of title + hour bucket of timestamp.
    """
    hour_bucket = timestamp.strftime("%Y%m%d%H") if timestamp else "unknown"
    raw = f"{source}|{title[:60].lower()}|{hour_bucket}"
    return hashlib.sha256(raw.encode()).hexdigest()


# ── raw_events CRUD ───────────────────────────────────────────────────────────

def insert_raw_event(event: dict[str, Any]) -> bool:
    """
    Insert a raw event into raw_events collection.
    Returns True if inserted, False if it was a duplicate (silently skipped).

    Expected fields:
        source, title, description, link, timestamp, raw_content, dedup_hash
    """
    event.setdefault("is_processed", False)
    event.setdefault("created_at", datetime.now(timezone.utc))

    try:
        _col("raw_events").insert_one(event)
        logger.debug(f"[raw_events] Inserted: {event.get('title', '')[:60]}")
        return True
    except Exception as e:
        if "duplicate key" in str(e).lower() or "E11000" in str(e):
            logger.debug(f"[raw_events] Duplicate skipped: {event.get('dedup_hash', '')[:12]}")
            return False
        logger.error(f"[raw_events] Insert error: {e}")
        return False


def get_unprocessed_events(limit: int = 100) -> list[dict]:
    """
    Fetch raw events that have not yet been classified + geo-resolved.
    Returns at most `limit` events, oldest first.
    """
    cursor = (
        _col("raw_events")
        .find({"is_processed": False})
        .sort("created_at", 1)
        .limit(limit)
    )
    return list(cursor)


def mark_raw_event_processed(event_id: ObjectId) -> None:
    """Mark a raw event as processed so the pipeline doesn't re-process it."""
    _col("raw_events").update_one(
        {"_id": event_id},
        {"$set": {"is_processed": True}}
    )


def count_raw_events(processed: bool | None = None) -> int:
    """Count raw events — optionally filter by processed status."""
    query = {} if processed is None else {"is_processed": processed}
    return _col("raw_events").count_documents(query)


# ── processed_events CRUD ─────────────────────────────────────────────────────

def insert_processed_event(event: dict[str, Any]) -> ObjectId | None:
    """
    Insert a fully classified + geo-resolved event.
    Returns the new document's ObjectId, or None on error.

    Expected fields:
        raw_event_id, disaster_type, location (with geo GeoJSON),
        severity, confidence, source, source_count, timestamp
    """
    event.setdefault("is_active", True)
    event.setdefault("source_count", 1)
    event.setdefault("cluster_id", None)
    event.setdefault("created_at", datetime.now(timezone.utc))

    try:
        result: InsertOneResult = _col("processed_events").insert_one(event)
        logger.info(
            f"[processed_events] Inserted: {event.get('disaster_type')} "
            f"@ {event.get('location', {}).get('name', 'unknown')} "
            f"[{event.get('severity')}]"
        )
        return result.inserted_id
    except Exception as e:
        logger.error(f"[processed_events] Insert error: {e}")
        return None


def increment_source_count(event_id: ObjectId, new_confidence: float) -> None:
    """
    Merge a duplicate event by incrementing its source_count
    and updating confidence to the higher value.
    """
    _col("processed_events").update_one(
        {"_id": event_id},
        {
            "$inc": {"source_count": 1},
            "$max": {"confidence": new_confidence},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        }
    )


def find_nearby_event(
    disaster_type: str,
    lon: float,
    lat: float,
    radius_m: int = 50_000,
    hours: int = 12,
) -> dict | None:
    """
    Find an existing processed event of the same disaster type
    within `radius_m` metres and `hours` hours (for deduplication).

    MongoDB $near requires [longitude, latitude] order.
    """
    from datetime import timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    return _col("processed_events").find_one({
        "disaster_type": disaster_type,
        "is_active": True,
        "timestamp": {"$gte": cutoff},
        "location.geo": {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat],   # ← GeoJSON: [lon, lat]
                },
                "$maxDistance": radius_m,
            }
        },
    })


def get_processed_events(
    disaster_type: str | None = None,
    severity: str | None = None,
    state: str | None = None,
    hours: int = 48,
    limit: int = 200,
) -> list[dict]:
    """
    Query processed events with optional filters.
    Defaults to events from the last 48 hours.
    """
    from datetime import timedelta

    query: dict[str, Any] = {
        "is_active": True,
        "timestamp": {"$gte": datetime.now(timezone.utc) - timedelta(hours=hours)},
    }
    if disaster_type:
        query["disaster_type"] = disaster_type
    if severity:
        query["severity"] = severity
    if state:
        query["location.state"] = {"$regex": state, "$options": "i"}

    return list(
        _col("processed_events")
        .find(query)
        .sort("timestamp", -1)
        .limit(limit)
    )


def get_event_by_id(event_id: str) -> dict | None:
    """Fetch a single processed event by its string ID."""
    try:
        return _col("processed_events").find_one({"_id": ObjectId(event_id)})
    except Exception:
        return None


def get_stats() -> dict:
    """
    Aggregate summary stats for the dashboard and /api/stats endpoint.
    Returns counts by disaster type, severity, and top states.
    """
    pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {
            "_id": {
                "disaster_type": "$disaster_type",
                "severity": "$severity",
            },
            "count": {"$sum": 1},
        }},
    ]
    agg = list(_col("processed_events").aggregate(pipeline))

    by_type: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    for row in agg:
        dtype = row["_id"].get("disaster_type", "unknown")
        sev = row["_id"].get("severity", "LOW")
        by_type[dtype] = by_type.get(dtype, 0) + row["count"]
        by_severity[sev] = by_severity.get(sev, 0) + row["count"]

    return {
        "total_events": sum(by_type.values()),
        "by_type": by_type,
        "by_severity": by_severity,
        "raw_pending": count_raw_events(processed=False),
    }


# ── alerts CRUD ───────────────────────────────────────────────────────────────

def insert_alert(alert: dict[str, Any]) -> ObjectId | None:
    """Insert a generated alert. Returns its ObjectId."""
    alert.setdefault("is_read", False)
    alert.setdefault("created_at", datetime.now(timezone.utc))

    try:
        result = _col("alerts").insert_one(alert)
        logger.info(f"[alerts] Created: {alert.get('message', '')[:60]}")
        return result.inserted_id
    except Exception as e:
        logger.error(f"[alerts] Insert error: {e}")
        return None


def get_recent_alerts(limit: int = 50) -> list[dict]:
    """Fetch the most recent alerts, newest first."""
    return list(
        _col("alerts").find().sort("created_at", -1).limit(limit)
    )


def mark_alert_read(alert_id: ObjectId) -> None:
    _col("alerts").update_one({"_id": alert_id}, {"$set": {"is_read": True}})


# ── geo_cache CRUD ────────────────────────────────────────────────────────────

def get_geo_cache(query: str) -> dict | None:
    """Check if a location query is already cached."""
    return _col("geo_cache").find_one({"_id": query})


def set_geo_cache(query: str, lat: float, lon: float, display_name: str) -> None:
    """Cache a Nominatim result to avoid repeat API calls."""
    _col("geo_cache").update_one(
        {"_id": query},
        {"$set": {
            "lat": lat,
            "lon": lon,
            "display_name": display_name,
            "cached_at": datetime.now(timezone.utc),
        }},
        upsert=True,
    )
