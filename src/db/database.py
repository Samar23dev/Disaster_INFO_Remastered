"""
src/db/database.py
──────────────────
MongoDB connection manager + collection/index initialisation.

Usage:
    from src.db.database import get_db, init_collections

    db = get_db()
    collection = db["raw_events"]
"""

import logging
import os

from dotenv import load_dotenv
from pymongo import ASCENDING, GEOSPHERE, MongoClient
from pymongo.database import Database

load_dotenv()

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB: str = os.getenv("MONGO_DB", "disaster_db")

# ── Singleton state ───────────────────────────────────────────────────────────
_client: MongoClient | None = None
_db: Database | None = None


# ── Connection ────────────────────────────────────────────────────────────────

def get_client() -> MongoClient:
    """Return (or create) the shared MongoClient instance."""
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Ping to verify connection early — fail fast if MongoDB isn't running
        _client.admin.command("ping")
        logger.info(f"✅ MongoDB connected → {MONGO_URI}")
    return _client


def get_db() -> Database:
    """Return the application database handle."""
    global _db
    if _db is None:
        _db = get_client()[MONGO_DB]
    return _db


# ── Index & Collection Initialisation ─────────────────────────────────────────

def init_collections() -> None:
    """
    Create all collections and their indexes on startup.
    Safe to call multiple times — MongoDB ignores duplicate index creation.
    """
    db = get_db()

    # ── raw_events ────────────────────────────────────────────────────────────
    raw = db["raw_events"]
    raw.create_index("dedup_hash", unique=True)   # prevents duplicate inserts
    raw.create_index("is_processed")              # fast fetch of pending items
    raw.create_index([("created_at", ASCENDING)]) # time-sorted queries

    # ── processed_events ──────────────────────────────────────────────────────
    processed = db["processed_events"]
    # 2dsphere index is REQUIRED for all $near and $geoWithin queries
    processed.create_index([("location.geo", GEOSPHERE)])
    processed.create_index("disaster_type")
    processed.create_index("severity")
    processed.create_index("is_active")
    processed.create_index([("timestamp", ASCENDING)])

    # ── alerts ────────────────────────────────────────────────────────────────
    alerts = db["alerts"]
    alerts.create_index("event_id")
    alerts.create_index([("created_at", ASCENDING)])
    alerts.create_index("is_read")

    # ── geo_cache ─────────────────────────────────────────────────────────────
    # Uses query string as _id → O(1) lookup, no extra index needed
    db["geo_cache"].create_index([("cached_at", ASCENDING)])

    logger.info("✅ MongoDB collections and indexes initialised.")


# ── Teardown ──────────────────────────────────────────────────────────────────

def close_connection() -> None:
    """Close the MongoDB connection cleanly on shutdown."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed.")
