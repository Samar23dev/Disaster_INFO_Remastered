"""GET /api/alerts"""

from fastapi import APIRouter, Query
from src.db.crud import get_recent_alerts

router = APIRouter(tags=["Alerts"])


@router.get("/alerts")
def list_alerts(limit: int = Query(50, ge=1, le=200)):
    alerts = get_recent_alerts(limit=limit)
    for a in alerts:
        a["_id"] = str(a["_id"])
        if a.get("event_id"):
            a["event_id"] = str(a["event_id"])
    return {"count": len(alerts), "alerts": alerts}
