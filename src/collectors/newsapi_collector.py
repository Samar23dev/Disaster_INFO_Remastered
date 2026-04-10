"""
src/collectors/newsapi_collector.py
────────────────────────────────────
Fetches disaster-related news from NewsAPI.org and inserts new raw events.

Free tier limits:
  - 100 requests per day
  - At 15-minute intervals: 96 requests/day — safely within limit
  - Results from the last 24 hours only (free tier restriction)

Search strategy:
  - Query: disaster-specific keywords (flood, earthquake, cyclone, etc.)
  - Country: in (India only)
  - Language: en
  - Sort: publishedAt (newest first)

Schedule: every 15 minutes (configured in scheduler/jobs.py)

Env:
    NEWS_API_KEY — required, set in .env
"""

import logging
import os
import time
from datetime import datetime, timezone

import httpx

from src.db.crud import insert_raw_event
from src.processors.deduplicator import prepare_event
from src.processors.keyword_filter import is_disaster_related
from src.processors.normalizer import normalize_newsapi

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
NEWS_API_BASE_URL: str = "https://newsapi.org/v2/everything"
REQUEST_TIMEOUT: int = 15
PAGE_SIZE: int = 100  # max per request on free tier

# Search query — targets Indian disaster events specifically
# We use 'everything' endpoint + country isn't available there, so we use 'in India' in q
SEARCH_QUERIES: list[str] = [
    "flood OR earthquake OR cyclone India",
    "landslide OR heatwave OR drought India",
    "tsunami OR storm OR disaster India",
    "NDMA OR cloudburst OR wildfire India",
]

INTER_QUERY_DELAY_SEC: float = 1.0


# ── API Caller ────────────────────────────────────────────────────────────────

def _fetch_articles(query: str) -> list[dict]:
    """
    Call the NewsAPI /everything endpoint for a given query string.

    Args:
        query: Search query string

    Returns:
        List of article dicts from the API response, or [] on any error.
    """
    if not NEWS_API_KEY:
        logger.error("[NewsAPI] NEWS_API_KEY not set in .env — skipping.")
        return []

    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": PAGE_SIZE,
        "apiKey": NEWS_API_KEY,
    }

    try:
        response = httpx.get(NEWS_API_BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
    except httpx.RequestError as e:
        logger.warning(f"[NewsAPI] Network error for query '{query[:40]}': {e}")
        return []

    if response.status_code == 401:
        logger.error("[NewsAPI] Invalid API key (401). Check NEWS_API_KEY in .env.")
        return []

    if response.status_code == 429:
        logger.warning("[NewsAPI] Rate limit hit (429). Will retry next cycle.")
        return []

    if response.status_code != 200:
        logger.warning(f"[NewsAPI] HTTP {response.status_code} for query: {query[:40]}")
        return []

    data = response.json()
    if data.get("status") != "ok":
        logger.warning(f"[NewsAPI] API error: {data.get('message', 'unknown')}")
        return []

    articles = data.get("articles", [])
    logger.debug(f"[NewsAPI] Query '{query[:40]}' → {len(articles)} articles.")
    return articles


# ── Main Collection Function ──────────────────────────────────────────────────

def run_newsapi_collection() -> int:
    """
    Run all search queries, filter for disaster relevance, and insert new events.

    Returns:
        Total number of new events inserted.
    """
    logger.info("[NewsAPI] Starting collection cycle...")

    if not NEWS_API_KEY:
        logger.warning("[NewsAPI] Skipping — NEWS_API_KEY not configured.")
        return 0

    seen_urls: set[str] = set()   # deduplicate within this cycle across queries
    total_inserted = 0

    for i, query in enumerate(SEARCH_QUERIES):
        articles = _fetch_articles(query)

        for article in articles:
            url = article.get("url", "")
            title = article.get("title", "") or ""
            description = article.get("description", "") or article.get("content", "") or ""

            # Skip "[Removed]" articles (NewsAPI placeholder for deleted content)
            if title.strip() == "[Removed]" or not title:
                continue

            # Skip cross-cycle URL duplicates (DB dedup handles the rest)
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)

            # ── Keyword pre-filter ────────────────────────────────────────────
            if not is_disaster_related(title, description):
                continue

            # ── Normalize + stamp + insert ────────────────────────────────────
            normalized = normalize_newsapi(article)
            event = prepare_event(normalized)

            if insert_raw_event(event):
                total_inserted += 1
                logger.info(f"[NewsAPI] ✅ Inserted: {title[:80]}")

        # Courtesy delay between queries
        if i < len(SEARCH_QUERIES) - 1:
            time.sleep(INTER_QUERY_DELAY_SEC)

    logger.info(f"[NewsAPI] Collection done — {total_inserted} new events inserted.")
    return total_inserted
