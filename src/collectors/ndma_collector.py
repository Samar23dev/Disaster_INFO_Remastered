"""
src/collectors/ndma_collector.py
─────────────────────────────────
Fetches and parses the NDMA (National Disaster Management Authority) CAP
(Common Alerting Protocol) XML feed and inserts new events into raw_events.

NDMA CAP Feed URL:
    https://sachet.ndma.gov.in/cap_public_website/FetchAllIndiaCurrentAlert

Behavior:
- Uses ETag / Last-Modified caching to avoid re-downloading unchanged feeds
- Filters through keyword_filter before inserting
- Normalizes to common schema, stamps dedup_hash, inserts via crud

Schedule: every 3 minutes (configured in scheduler/jobs.py)
"""

import logging
import os
import time
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

import httpx

from src.db.crud import insert_raw_event
from src.processors.deduplicator import prepare_event
from src.processors.keyword_filter import is_disaster_related
from src.processors.normalizer import normalize_ndma

logger = logging.getLogger(__name__)

# ── Feed Configuration ────────────────────────────────────────────────────────

NDMA_FEED_URL: str = os.getenv(
    "NDMA_FEED_URL",
    "https://sachet.ndma.gov.in/cap_public_website/FetchAllIndiaCurrentAlert",
)
REQUEST_TIMEOUT: int = 15  # seconds

# CAP XML namespace
CAP_NS = "urn:oasis:names:tc:emergency:cap:1.2"

# ETag cache — avoids re-parsing unchanged feeds
_last_etag: str = ""
_last_modified: str = ""


# ── XML Parser ────────────────────────────────────────────────────────────────

def _parse_cap_xml(xml_text: str) -> list[dict]:
    """
    Parse a CAP XML feed into a list of alert dicts.

    CAP structure:
        <feed>
          <entry>
            <title> ... </title>
            <cap:headline> ... </cap:headline>
            <cap:description> ... </cap:description>
            <cap:sent> ... </cap:sent>
            <link href="..." />
          </entry>
        </feed>

    Returns list of parsed dicts with keys: title, headline, description, sent, link
    """
    alerts = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.error(f"[NDMA] XML parse error: {e}")
        return alerts

    # Handle both Atom feed and CAP root elements
    ns = {"cap": CAP_NS, "atom": "http://www.w3.org/2005/Atom"}

    entries = root.findall(".//atom:entry", ns) or root.findall(".//entry")

    for entry in entries:
        def _text(tag: str) -> str:
            el = entry.find(tag, ns) or entry.find(tag.split(":")[-1])
            return el.text.strip() if el is not None and el.text else ""

        # CAP-specific fields under cap: namespace
        headline = _text("cap:headline") or _text("headline")
        description = _text("cap:description") or _text("description")
        sent = _text("cap:sent") or _text("sent") or _text("atom:updated") or _text("updated")
        title = _text("atom:title") or _text("title")
        event = _text("cap:event") or _text("event")

        # Link href attribute
        link_el = entry.find("atom:link", ns) or entry.find("link")
        link = ""
        if link_el is not None:
            link = link_el.get("href", "") or link_el.text or ""

        alerts.append({
            "headline": headline or title or event,
            "title": title or headline or event,
            "description": description,
            "event": event,
            "sent": sent,
            "link": link,
        })

    logger.debug(f"[NDMA] Parsed {len(alerts)} CAP entries from XML")
    return alerts


# ── Fallback: RSS-style Atom feed ─────────────────────────────────────────────

def _try_atom_fallback(xml_text: str) -> list[dict]:
    """
    Some NDMA endpoints return a simple Atom/RSS feed.
    This fallback handles the simpler <item> or <entry> structure.
    """
    alerts = []
    try:
        import feedparser
        feed = feedparser.parse(xml_text)
        for entry in feed.entries:
            alerts.append({
                "headline": getattr(entry, "title", ""),
                "title": getattr(entry, "title", ""),
                "description": getattr(entry, "summary", ""),
                "sent": getattr(entry, "published", ""),
                "link": getattr(entry, "link", ""),
            })
    except Exception as e:
        logger.debug(f"[NDMA] Atom fallback also failed: {e}")
    return alerts


# ── Main Collection Function ──────────────────────────────────────────────────

def run_ndma_collection() -> int:
    """
    Fetch NDMA CAP feed, parse, filter, and insert new events.

    Returns:
        Number of new events inserted
    """
    global _last_etag, _last_modified

    logger.info("[NDMA] Starting collection cycle...")

    headers: dict[str, str] = {
        "User-Agent": "GeoPulse-DisasterMonitor/1.0 (research project)",
        "Accept": "application/xml, application/atom+xml, text/xml, */*",
    }
    if _last_etag:
        headers["If-None-Match"] = _last_etag
    if _last_modified:
        headers["If-Modified-Since"] = _last_modified

    # ── HTTP Request ──────────────────────────────────────────────────────────
    try:
        response = httpx.get(NDMA_FEED_URL, headers=headers, timeout=REQUEST_TIMEOUT,
                              follow_redirects=True)
    except httpx.RequestError as e:
        logger.warning(f"[NDMA] Network error: {e}")
        return 0

    if response.status_code == 304:
        logger.info("[NDMA] Feed unchanged (304 Not Modified). Skipping.")
        return 0

    if response.status_code != 200:
        logger.warning(f"[NDMA] Unexpected HTTP {response.status_code}")
        return 0

    # Update ETag cache
    _last_etag = response.headers.get("ETag", "")
    _last_modified = response.headers.get("Last-Modified", "")

    xml_text = response.text
    if not xml_text.strip():
        logger.warning("[NDMA] Empty response body.")
        return 0

    # ── Parse ─────────────────────────────────────────────────────────────────
    cap_entries = _parse_cap_xml(xml_text)
    if not cap_entries:
        logger.info("[NDMA] No CAP entries parsed — trying Atom fallback.")
        cap_entries = _try_atom_fallback(xml_text)

    inserted_count = 0
    for entry in cap_entries:
        title = entry.get("title", "") or entry.get("headline", "")
        description = entry.get("description", "")

        # ── Keyword pre-filter ────────────────────────────────────────────────
        if not is_disaster_related(title, description):
            logger.debug(f"[NDMA] Filtered out (no disaster keywords): {title[:60]}")
            continue

        # ── Normalize + stamp hash + insert ───────────────────────────────────
        normalized = normalize_ndma(entry, raw_xml=xml_text[:2000])
        event = prepare_event(normalized)

        if insert_raw_event(event):
            inserted_count += 1
            logger.info(f"[NDMA] ✅ Inserted: {title[:80]}")

    logger.info(
        f"[NDMA] Collection done — {len(cap_entries)} parsed, {inserted_count} new events inserted."
    )
    return inserted_count
