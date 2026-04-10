"""
src/collectors/rss_collector.py
────────────────────────────────
Fetches and parses RSS feeds from major Indian news sources.
Each entry is keyword-filtered, normalized, dedup-stamped, and inserted.

Sources:
  - Times of India (National/India news)
  - The Hindu (National)
  - Indian Express (National)
  - NDTV (Disaster/India)
  - Hindustan Times (India)

Schedule: every 8 minutes (configured in scheduler/jobs.py)

Note:
  feedparser handles all RSS/Atom variants including malformed XML gracefully.
"""

import logging
import time
from dataclasses import dataclass

import feedparser

from src.db.crud import insert_raw_event
from src.processors.deduplicator import prepare_event
from src.processors.keyword_filter import is_disaster_related
from src.processors.normalizer import normalize_rss

logger = logging.getLogger(__name__)


# ── Feed Registry ─────────────────────────────────────────────────────────────

@dataclass
class RSSFeed:
    name: str
    url: str


RSS_FEEDS: list[RSSFeed] = [
    # Times of India — India news (has dedicated disaster/weather section)
    RSSFeed("TOI", "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms"),
    # The Hindu — National news
    RSSFeed("TheHindu", "https://www.thehindu.com/news/national/feeder/default.rss"),
    # Indian Express — India news
    RSSFeed("IndianExpress", "https://indianexpress.com/section/india/feed/"),
    # NDTV — India news
    RSSFeed("NDTV", "https://feeds.feedburner.com/ndtvnews-india-news"),
    # Hindustan Times
    RSSFeed("HindustanTimes", "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml"),
]

# Respect Nominatim-style courtesy: don't hammer RSS servers
INTER_FEED_DELAY_SEC: float = 1.0
REQUEST_TIMEOUT: int = 15


# ── Per-Feed Collection ───────────────────────────────────────────────────────

def _collect_feed(feed: RSSFeed) -> int:
    """
    Fetch and process a single RSS feed.

    Returns:
        Number of new events inserted from this feed.
    """
    logger.info(f"[RSS] Fetching {feed.name}: {feed.url}")

    try:
        parsed = feedparser.parse(
            feed.url,
            agent="GeoPulse-DisasterMonitor/1.0 (research project)",
            request_headers={"Accept": "application/rss+xml, application/atom+xml, */*"},
        )
    except Exception as e:
        logger.warning(f"[RSS:{feed.name}] feedparser error: {e}")
        return 0

    if parsed.bozo and parsed.bozo_exception:
        # bozo=True means feed has XML issues — log but still try to process
        logger.debug(f"[RSS:{feed.name}] Bozo feed (malformed XML): {parsed.bozo_exception}")

    entries = parsed.entries
    if not entries:
        logger.info(f"[RSS:{feed.name}] No entries found.")
        return 0

    logger.info(f"[RSS:{feed.name}] {len(entries)} entries fetched.")
    inserted = 0

    for entry in entries:
        title = getattr(entry, "title", "") or ""
        description = (
            getattr(entry, "summary", "")
            or getattr(entry, "description", "")
            or ""
        )

        # ── Keyword pre-filter ────────────────────────────────────────────────
        if not is_disaster_related(title, description):
            continue

        # ── Normalize + dedup stamp + insert ──────────────────────────────────
        normalized = normalize_rss(entry, feed_url=feed.url)
        event = prepare_event(normalized)

        if insert_raw_event(event):
            inserted += 1
            logger.info(f"[RSS:{feed.name}] ✅ Inserted: {title[:80]}")

    logger.info(f"[RSS:{feed.name}] {inserted} new events from {len(entries)} entries.")
    return inserted


# ── Main Collection Function ──────────────────────────────────────────────────

def run_rss_collection() -> int:
    """
    Iterate through all registered RSS feeds and collect disaster events.

    Returns:
        Total number of new events inserted across all feeds.
    """
    logger.info("[RSS] Starting collection cycle...")
    total_inserted = 0

    for i, feed in enumerate(RSS_FEEDS):
        try:
            count = _collect_feed(feed)
            total_inserted += count
        except Exception as e:
            logger.error(f"[RSS:{feed.name}] Unexpected error: {e}", exc_info=True)

        # Courtesy delay between feeds (skip after last feed)
        if i < len(RSS_FEEDS) - 1:
            time.sleep(INTER_FEED_DELAY_SEC)

    logger.info(f"[RSS] Collection done — {total_inserted} total new events inserted.")
    return total_inserted
