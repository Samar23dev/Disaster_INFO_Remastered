"""
src/alerts/alert_engine.py
──────────────────────────
Continuously evaluates active 'processed_events' against risk thresholds.
If an event warrants a public alert, it inserts it into the `alerts` database collection.
"""

import logging

from src.alerts.risk_scorer import calculate_risk_score
from src.alerts.safety_advisor import get_safety_advice
from src.db.crud import (
    _col,
    get_processed_events,
    insert_alert,
)

logger = logging.getLogger(__name__)

# Minimum composite Risk Score (0-100) before triggering a database alert
ALERT_THRESHOLD = 45  


def check_and_generate_alerts() -> int:
    """
    Scans all recent processed events.
    Applies the Risk Engine math. If it breaches the ALERT_THRESHOLD,
    we lock in an Official Alert, query Gemini for safety protocols, and store it.
    
    Returns:
        Number of new alerts generated this cycle.
    """
    events = get_processed_events(hours=12, limit=2000)
    alerts_generated = 0
    
    for ev in events:
        # Check if we already alerted for this specific event to prevent spam
        # This is an efficient indexed check since `event_id` is linked.
        existing_alert = _col("alerts").find_one({"event_id": ev["_id"]})
        if existing_alert:
            continue
            
        # Compile mathematical risk score
        risk_score = calculate_risk_score(
            severity=ev.get("severity", "LOW"),
            confidence=float(ev.get("confidence", 0.0)),
            source_count=int(ev.get("source_count", 1))
        )
        
        # Threshold Check
        if risk_score >= ALERT_THRESHOLD:
            location_name = ev.get("location", {}).get("name", "Unknown Location")
            logger.warning(f"[Alert Engine] THRESHOLD BREACH (Score: {risk_score}): {ev['disaster_type']} @ {location_name}")
            
            # Request dynamic safety advice from LLM
            advice = get_safety_advice(ev["disaster_type"], ev["severity"])
            
            # Construct official alert
            from datetime import datetime, timezone
            alert_doc = {
                "event_id": ev["_id"],
                "disaster_type": ev["disaster_type"],
                "severity": ev["severity"],
                "risk_score": risk_score,
                "location_name": location_name,
                "cluster_id": ev.get("cluster_id"),
                "safety_advice": advice,
                "is_read": False,
                "created_at": datetime.now(timezone.utc)
            }
            
            success_id = insert_alert(alert_doc)
            if success_id:
                alerts_generated += 1
                
    if alerts_generated > 0:
        logger.info(f"[Alert Engine] Successfully fired {alerts_generated} new alerts.")
        
    return alerts_generated
