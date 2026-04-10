"""
src/processors/normalizer.py
─────────────────────────────
Converts raw data from all sources (NDMA, RSS, NewsAPI) into the
single canonical schema expected by raw_events collection.

Common schema:
    {
        "source":       str,       # "NDMA" | "TOI" | "TheHindu" | "IndianExpress" | "NewsAPI"
        "title":        str,
        "description":  str,
        "link":         str,
        "timestamp":    datetime (UTC, timezone-aware),
        "raw_content":  str,       # original XML/JSON as string
        "dedup_hash":   str,       # set by deduplicator.make_dedup_hash()
    }

Usage:
    from src.processors.normalizer import normalize_ndma, normalize_rss, normalize_newsapi
"""

import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_utc(dt: datetime | None) -> datetime:
    """Ensure a datetime is UTC-aware. Falls back to now() if None."""
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _clean_str(value: Any, max_len: int = 2000) -> str:
    """Strip whitespace, truncate to max_len, return empty string if None."""
    if not value:
        return ""
    return str(value).strip()[:max_len]


def _parse_rss_date(date_str: str) -> datetime:
    """
    Parse an RFC 2822 date string from RSS (e.g. 'Mon, 09 Apr 2025 10:00:00 +0530').
    Falls back to UTC now() on any parse error.
    """
    try:
        return parsedate_to_datetime(date_str).astimezone(timezone.utc)
    except Exception:
        logger.debug(f"[normalizer] Could not parse RSS date: {date_str!r}")
        return datetime.now(timezone.utc)


# ── NDMA Normalizer ───────────────────────────────────────────────────────────

def normalize_ndma(cap_entry: dict[str, Any], raw_xml: str = "") -> dict[str, Any]:
    """
    Normalize a single NDMA CAP alert entry into the common schema.

    Args:
        cap_entry:  Dict parsed from CAP XML (keys: title, description, link, sent, etc.)
        raw_xml:    Original XML string for archival

    Returns:
        Normalized event dict (without dedup_hash — set by deduplicator)
    """
    sent_raw = cap_entry.get("sent") or cap_entry.get("effective") or cap_entry.get("onset")
    try:
        ts = datetime.fromisoformat(str(sent_raw).replace("Z", "+00:00")) if sent_raw else None
    except ValueError:
        ts = None

    return {
        "source": "NDMA",
        "title": _clean_str(cap_entry.get("headline") or cap_entry.get("title"), 500),
        "description": _clean_str(
            cap_entry.get("description") or cap_entry.get("event"), 2000
        ),
        "link": _clean_str(cap_entry.get("identifier") or cap_entry.get("link"), 1000),
        "timestamp": _to_utc(ts),
        "raw_content": raw_xml[:5000] if raw_xml else "",
    }


# ── RSS Normalizer ────────────────────────────────────────────────────────────

# Maps feedparser source URL fragments → human-readable source names
_RSS_SOURCE_MAP: dict[str, str] = {
    "timesofindia": "TOI",
    "toi.in": "TOI",
    "thehindu": "TheHindu",
    "the-hindu": "TheHindu",
    "indianexpress": "IndianExpress",
    "indian-express": "IndianExpress",
    "ndtv": "NDTV",
    "hindustantimes": "HindustanTimes",
}


def _resolve_rss_source(feed_url: str) -> str:
    """Map a feed URL to its canonical source name."""
    url_lower = feed_url.lower()
    for key, name in _RSS_SOURCE_MAP.items():
        if key in url_lower:
            return name
    return "RSS"


def normalize_rss(entry: Any, feed_url: str = "") -> dict[str, Any]:
    """
    Normalize a feedparser entry into the common schema.

    Args:
        entry:    feedparser entry object (has .title, .summary, .link, .published)
        feed_url: The source RSS URL (used to infer source name)

    Returns:
        Normalized event dict
    """
    source_name = _resolve_rss_source(feed_url)

    # feedparser provides .published (RFC 2822 string) or .published_parsed (struct_time)
    ts: datetime
    if hasattr(entry, "published") and entry.published:
        ts = _parse_rss_date(entry.published)
    elif hasattr(entry, "updated") and entry.updated:
        ts = _parse_rss_date(entry.updated)
    else:
        ts = datetime.now(timezone.utc)

    title = _clean_str(getattr(entry, "title", ""), 500)
    summary = _clean_str(getattr(entry, "summary", "") or getattr(entry, "description", ""), 2000)
    link = _clean_str(getattr(entry, "link", ""), 1000)

    return {
        "source": source_name,
        "title": title,
        "description": summary,
        "link": link,
        "timestamp": ts,
        "raw_content": f"title={title}|link={link}|published={ts.isoformat()}",
    }


# ── NewsAPI Normalizer ────────────────────────────────────────────────────────

def normalize_newsapi(article: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize a single NewsAPI article dict into the common schema.

    Args:
        article: Dict from NewsAPI response['articles'] list
                 Keys: title, description, content, url, publishedAt, source

    Returns:
        Normalized event dict
    """
    published_at = article.get("publishedAt", "")
    try:
        ts: datetime = datetime.fromisoformat(
            published_at.replace("Z", "+00:00")
        ) if published_at else datetime.now(timezone.utc)
    except ValueError:
        ts = datetime.now(timezone.utc)

    title = _clean_str(article.get("title", ""), 500)
    description = _clean_str(
        article.get("description") or article.get("content", ""), 2000
    )
    link = _clean_str(article.get("url", ""), 1000)

    # NewsAPI provides source as {"id": ..., "name": ...}
    source_name = "NewsAPI"

    return {
        "source": source_name,
        "title": title,
        "description": description,
        "link": link,
        "timestamp": _to_utc(ts),
        "raw_content": (
            f"title={title}|desc={description[:200]}|url={link}|published={published_at}"
        ),
    }
