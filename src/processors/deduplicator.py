"""
src/processors/deduplicator.py
───────────────────────────────
Deduplication utilities for raw events.

The dedup strategy uses a SHA-256 hash of:
    source + title[:60].lower() + hour_bucket (YYYYMMDDHH)

This ensures:
- Same article from same source in the same hour = duplicate
- Same event re-published hours later = new entry (good — re-confirms event)
- Minor title variations in same hour = still caught as duplicate

Usage:
    from src.processors.deduplicator import stamp_dedup_hash

    event = normalize_rss(entry, feed_url)
    event = stamp_dedup_hash(event)      # attaches 'dedup_hash' key
    inserted = insert_raw_event(event)   # DB enforces uniqueness
"""

import logging

from src.db.crud import make_dedup_hash

logger = logging.getLogger(__name__)


def stamp_dedup_hash(event: dict) -> dict:
    """
    Compute and attach a `dedup_hash` field to a normalized event dict.

    Mutates the dict in-place AND returns it (for chaining).

    Args:
        event: A normalized event dict with keys: source, title, timestamp

    Returns:
        The same dict with 'dedup_hash' key added/overwritten.
    """
    event["dedup_hash"] = make_dedup_hash(
        source=event.get("source", ""),
        title=event.get("title", ""),
        timestamp=event.get("timestamp"),
    )
    return event


def prepare_event(event: dict) -> dict:
    """
    Convenience: stamp dedup hash and return the event ready for DB insert.

    Args:
        event: Normalized event dict (from any normalizer)

    Returns:
        Event dict with dedup_hash attached
    """
    return stamp_dedup_hash(event)
