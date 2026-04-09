"""GET /api/stats  and  GET /api/heatmap"""

from fastapi import APIRouter
from src.db.crud import get_stats, get_processed_events

router = APIRouter(tags=["Stats"])


@router.get("/stats")
def stats():
    return get_stats()


@router.get("/heatmap")
def heatmap():
    """
    Returns coordinate + weight data for map heatmap rendering.
    Weight is derived from severity: HIGH=3, MEDIUM=2, LOW=1.
    """
    SEVERITY_WEIGHT = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    events = get_processed_events(hours=48, limit=500)
    points = []
    for e in events:
        geo = e.get("location", {}).get("geo", {}).get("coordinates")
        if geo and len(geo) == 2:
            lon, lat = geo
            weight = SEVERITY_WEIGHT.get(e.get("severity", "LOW"), 1)
            points.append({"lat": lat, "lon": lon, "weight": weight})
    return {"count": len(points), "points": points}
