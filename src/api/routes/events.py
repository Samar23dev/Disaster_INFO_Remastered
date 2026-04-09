"""GET /api/events and GET /api/events/{id}"""

from fastapi import APIRouter, Query
from src.db.crud import get_processed_events, get_event_by_id, get_stats

router = APIRouter(tags=["Events"])


@router.get("/events")
def list_events(
    disaster_type: str | None = Query(None),
    severity: str | None = Query(None),
    state: str | None = Query(None),
    hours: int = Query(48, ge=1, le=720),
    limit: int = Query(100, ge=1, le=500),
):
    events = get_processed_events(
        disaster_type=disaster_type,
        severity=severity,
        state=state,
        hours=hours,
        limit=limit,
    )
    # Convert ObjectId → string for JSON serialisation
    for e in events:
        e["_id"] = str(e["_id"])
        if e.get("raw_event_id"):
            e["raw_event_id"] = str(e["raw_event_id"])
    return {"count": len(events), "events": events}


@router.get("/events/{event_id}")
def get_event(event_id: str):
    event = get_event_by_id(event_id)
    if not event:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Event not found")
    event["_id"] = str(event["_id"])
    return event
