"""
main.py
───────
Unified entry point for GeoPulse Intelligence.

Starts:
  1. APScheduler (background cron jobs — data collection + pipeline)
  2. FastAPI server (REST API on port 8000)

Run separately:
  streamlit run app.py        ← dashboard (port 8501)
"""

import logging
import os

import uvicorn
from dotenv import load_dotenv

from src.db.database import close_connection, init_collections
from src.scheduler.jobs import start_scheduler

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Entry ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        logger.info("🚀 GeoPulse Intelligence starting...")

        # Step 1: Initialise MongoDB collections + indexes
        init_collections()

        # Step 2: Start background scheduler (cron jobs)
        scheduler = start_scheduler()

        # Step 3: Start FastAPI (blocking — keeps process alive)
        logger.info("🌐 FastAPI starting on http://localhost:8000")
        logger.info("📊 Run dashboard: streamlit run app.py")

        from src.api.app import create_app
        app = create_app()
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=int(os.getenv("API_PORT", 8000)),
            log_level="warning",   # uvicorn logs suppressed; we use our own
        )

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.critical(f"Startup failed: {e}", exc_info=True)
    finally:
        close_connection()
        logger.info("Goodbye.")
