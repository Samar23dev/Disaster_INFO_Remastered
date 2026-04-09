"""
src/scheduler/jobs.py
─────────────────────
APScheduler job definitions — the "cron" layer of GeoPulse.

Jobs:
  - NDMA collector      → every 3 minutes
  - RSS collector       → every 8 minutes
  - NewsAPI collector   → every 15 minutes
  - Full pipeline       → every 10 minutes (classification + geo + alerts)
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


# ── Job functions (import lazily to avoid circular imports) ───────────────────

def _run_ndma_collection():
    try:
        from src.collectors.ndma_collector import run_ndma_collection
        run_ndma_collection()
    except Exception as e:
        logger.error(f"[Scheduler] NDMA collection failed: {e}")


def _run_rss_collection():
    try:
        from src.collectors.rss_collector import run_rss_collection
        run_rss_collection()
    except Exception as e:
        logger.error(f"[Scheduler] RSS collection failed: {e}")


def _run_newsapi_collection():
    try:
        from src.collectors.newsapi_collector import run_newsapi_collection
        run_newsapi_collection()
    except Exception as e:
        logger.error(f"[Scheduler] NewsAPI collection failed: {e}")


def _run_full_pipeline():
    try:
        from src.classifiers.pipeline import run_pipeline
        run_pipeline()
    except Exception as e:
        logger.error(f"[Scheduler] Pipeline failed: {e}")


# ── Scheduler setup ───────────────────────────────────────────────────────────

def start_scheduler() -> BackgroundScheduler:
    """
    Create and start the APScheduler instance.
    Runs all jobs in the background — main thread stays free for FastAPI.
    """
    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")

    scheduler.add_job(
        _run_ndma_collection,
        trigger=IntervalTrigger(minutes=3),
        id="ndma_collector",
        name="NDMA CAP Feed Collector",
        replace_existing=True,
    )

    scheduler.add_job(
        _run_rss_collection,
        trigger=IntervalTrigger(minutes=8),
        id="rss_collector",
        name="RSS Feed Collector",
        replace_existing=True,
    )

    scheduler.add_job(
        _run_newsapi_collection,
        trigger=IntervalTrigger(minutes=15),
        id="newsapi_collector",
        name="NewsAPI Collector",
        replace_existing=True,
    )

    scheduler.add_job(
        _run_full_pipeline,
        trigger=IntervalTrigger(minutes=10),
        id="full_pipeline",
        name="Classification + Geo + Alert Pipeline",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("⏰ Scheduler started. Jobs: NDMA(3m) · RSS(8m) · NewsAPI(15m) · Pipeline(10m)")
    return scheduler
