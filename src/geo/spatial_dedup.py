"""
src/geo/spatial_dedup.py
────────────────────────
Manages MongoDB 2dsphere proximity deduplication logic natively.

Checks the database to see if an identical disaster type occurred within 
X hours and Y kilometers. If so, increments the source count instead of branching.
"""

import logging
from typing import Any

from src.db.crud import find_nearby_event, increment_source_count

logger = logging.getLogger(__name__)

def deduplicate_spatial(
    disaster_type: str, 
    lat: float, 
    lon: float, 
    confidence: float,
    radius_km: int = 50,
    hours: int = 12
) -> str | None:
    """
    Check if a nearby event exists. If it does, automatically merge it 
    by bumping the database 'source_count' and maximum 'confidence' metric.
    
    Returns:
        ObjectId (as string) of the merged target event if merged.
        None if this is a brand new unique spatial event.
    """
    
    # MongoDB calculates strictly in meters natively
    radius_m = radius_km * 1000
    
    # DB handles the heavy floating point haversine computations centrally!
    existing = find_nearby_event(disaster_type, lon=lon, lat=lat, radius_m=radius_m, hours=hours)
    
    if existing:
        target_id = existing["_id"]
        logger.info(f"[Spatial Dedup] Merging {disaster_type} into active cluster {target_id}")
        increment_source_count(target_id, confidence)
        return str(target_id)
        
    return None
