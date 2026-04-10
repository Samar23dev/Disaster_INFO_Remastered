"""
src/geo/geo_resolver.py
───────────────────────
Converts location strings (e.g. "Mumbai, India") into GeoJSON latitude/longitude
using Nominatim via the Geopy library.

Respects rate limits (1 req/sec) and hits MongoDB `geo_cache` locally
first before making any network calls.
"""

import logging
import time
from typing import Any

from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim

from src.db.crud import get_geo_cache, set_geo_cache

logger = logging.getLogger(__name__)

# Single instance. Nominatim requires a genuine user agent.
_geolocator = None

def get_geolocator():
    global _geolocator
    if _geolocator is None:
        _geolocator = Nominatim(user_agent="GeoPulse_DisasterMonitor_v1")
    return _geolocator

def resolve_location(loc_name: str, country_context: str = "India") -> tuple[float, float, str] | None:
    """
    Resolve a location name into (lat, lon, display_name).
    Hits the database cache first to prevent redundant API calls.
    
    Args:
        loc_name: Extracted entity like "Assam" or "Mumbai"
        country_context: Added dynamically to limit scope
        
    Returns:
        (latitude, longitude, formatted_address) or None if unresolved.
    """
    if not loc_name:
        return None
        
    # Build query string
    query_str = f"{loc_name}, {country_context}"
    cache_key = query_str.lower().strip()
    
    # 1. Check MongoDB cache first (O(1) lookup on _id)
    cached = get_geo_cache(cache_key)
    if cached:
        logger.debug(f"[Geo] Cache hit: {loc_name} -> {cached['lat']}, {cached['lon']}")
        return float(cached["lat"]), float(cached["lon"]), cached["display_name"]
        
    # 2. Query Nominatim API (cache miss)
    geolocator = get_geolocator()
    
    # Sleep to respect 1 request/second Nominatim limits
    time.sleep(1.1) 
    
    try:
        logger.info(f"[Geo] API Request: Nominatim querying {query_str}...")
        location = geolocator.geocode(query_str, timeout=10)
        
        if location:
            lat, lon = location.latitude, location.longitude
            display = location.address
            
            # 3. Save result globally in cache
            set_geo_cache(cache_key, lat, lon, display)
            return lat, lon, display
            
    except GeocoderTimedOut:
        logger.warning(f"[Geo] Timeout resolving {query_str}")
    except Exception as e:
        logger.error(f"[Geo] Error resolving {query_str}: {e}")
        
    return None
