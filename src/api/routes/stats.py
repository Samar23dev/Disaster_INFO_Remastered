"""GET /api/stats  and  GET /api/heatmap  and  GET /api/risk/{location}"""

from fastapi import APIRouter, HTTPException
from src.db.crud import get_stats, get_processed_events
from src.alerts.risk_scorer import calculate_risk_score

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


@router.get("/risk/{location}")
def get_risk_score(location: str):
    """
    Calculate risk score for a specific location.
    Returns aggregated risk based on recent events in that area.
    """
    # Search for events matching the location name (case-insensitive)
    events = get_processed_events(hours=24, limit=100)
    
    # Filter events for this location
    location_events = [
        e for e in events 
        if location.lower() in e.get("location", {}).get("name", "").lower()
    ]
    
    if not location_events:
        raise HTTPException(
            status_code=404, 
            detail=f"No recent events found for location: {location}"
        )
    
    # Calculate aggregate risk score
    total_risk = 0
    severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    
    for event in location_events:
        severity = event.get("severity", "LOW")
        confidence = event.get("confidence", 0.5)
        source_count = event.get("source_count", 1)
        
        risk = calculate_risk_score(severity, confidence, source_count)
        total_risk += risk
        severity_counts[severity] += 1
    
    avg_risk = total_risk / len(location_events) if location_events else 0
    
    # Determine risk level
    if avg_risk >= 70:
        risk_level = "CRITICAL"
    elif avg_risk >= 50:
        risk_level = "HIGH"
    elif avg_risk >= 30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    return {
        "location": location,
        "risk_score": round(avg_risk, 2),
        "risk_level": risk_level,
        "event_count": len(location_events),
        "severity_breakdown": severity_counts,
        "time_window_hours": 24
    }

