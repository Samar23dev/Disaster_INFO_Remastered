"""
src/api/app.py
──────────────
FastAPI application factory.

Exposes REST endpoints that Streamlit uses now, and Flutter will use later.
Run via main.py — do not run this file directly.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    app = FastAPI(
        title="GeoPulse Intelligence API",
        description="Real-time disaster monitoring system — India focused",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # Allow Streamlit (port 8501) and future Flutter app to call the API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],   # Tighten this for production
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register route modules
    from src.api.routes.events import router as events_router
    from src.api.routes.alerts import router as alerts_router
    from src.api.routes.stats import router as stats_router

    app.include_router(events_router, prefix="/api")
    app.include_router(alerts_router, prefix="/api")
    app.include_router(stats_router,  prefix="/api")

    @app.get("/", tags=["Health"])
    def health_check():
        return {"status": "ok", "service": "GeoPulse Intelligence"}

    return app
