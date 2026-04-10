"""
src/classifiers/pipeline.py
───────────────────────────
Orchestrates the full event-processing pipeline:
  1. Rule Classifier  (regex, < 1 ms)
  2. ML Classifier    (distilbart-mnli-12-3, zero-shot)
  3. LLM Fallback     (Gemini 1.5 Flash, capped at LLM_MAX_CALLS_PER_CYCLE)
  4. Severity Detector
  5. Geo Resolution   (spaCy NER → alias normaliser → Nominatim/cache)
  6. Spatial Dedup    (MongoDB $near, 50 km / 12 hr window)
  7. DBSCAN Clustering (post-pass over all active events)
"""

import logging
import os
from datetime import datetime

from src.classifiers.llm_fallback import llm_classify
from src.classifiers.ml_classifier import ml_classify
from src.classifiers.rule_classifier import rule_classify
from src.classifiers.severity_detector import detect_severity

# Phase 3 Extractor Logic
from src.geo.ner_extractor import extract_locations
from src.geo.loc_normalizer import normalize_location
from src.geo.geo_resolver import resolve_location
from src.geo.spatial_dedup import deduplicate_spatial
from src.geo.clusterer import run_clustering

# Phase 4 Alerts Engine
from src.alerts.alert_engine import check_and_generate_alerts

from src.db.crud import (
    get_unprocessed_events,
    insert_processed_event,
    mark_raw_event_processed,
)

logger = logging.getLogger(__name__)

# Config
RULE_THRESHOLD = float(os.getenv("RULE_CONFIDENCE_THRESHOLD", "0.75"))
ML_THRESHOLD = float(os.getenv("ML_CONFIDENCE_THRESHOLD", "0.55"))
LLM_MAX_CALLS = int(os.getenv("LLM_MAX_CALLS_PER_CYCLE", "10"))
DEDUP_RADIUS_KM = int(os.getenv("DEDUP_RADIUS_KM", "50"))
DEDUP_TIME_WINDOW = int(os.getenv("DEDUP_TIME_WINDOW_HOURS", "12"))

# Module-level counter — reset to 0 at the start of every pipeline cycle
_llm_calls_this_cycle: int = 0

def _classify_event(title: str, description: str) -> tuple[str, float]:
    """
    Run the 3-stage classification waterfall.
    Returns (disaster_type, confidence).
    """
    global _llm_calls_this_cycle
    
    dtype, conf = rule_classify(title, description)
    if conf >= RULE_THRESHOLD:
        logger.debug(f"[Pipeline] Rule matched: {dtype} ({conf})")
        return dtype, conf

    dtype, conf = ml_classify(title, description)
    if conf >= ML_THRESHOLD:
        logger.debug(f"[Pipeline] ML matched: {dtype} ({conf})")
        return dtype, conf

    if _llm_calls_this_cycle < LLM_MAX_CALLS:
        _llm_calls_this_cycle += 1
        llm_dtype, llm_conf = llm_classify(title, description)
        if llm_conf > conf:
            logger.debug(f"[Pipeline] LLM matched: {llm_dtype} ({llm_conf})")
            return llm_dtype, llm_conf

    return dtype, conf

def run_pipeline() -> int:
    """
    Fetch raw events, classify, geometrically resolve, spatially deduplicate, 
    and perform regional DBSCAN assignments.
    """
    global _llm_calls_this_cycle
    _llm_calls_this_cycle = 0
    
    logger.info("[Pipeline] Starting classification cycle...")
    raw_events = get_unprocessed_events(limit=50)
    
    if not raw_events:
        logger.info("[Pipeline] No unprocessed events. Checking clustering mechanics...")
        run_clustering()
        return 0
        
    logger.info(f"[Pipeline] Processing {len(raw_events)} events...")
    processed_count = 0
    
    for raw in raw_events:
        title = raw.get("title", "")
        description = raw.get("description", "")
        
        dtype, conf = _classify_event(title, description)
        
        if conf < 0.3 or dtype == "unknown":
            logger.info(f"[Pipeline] Dropped low-confidence event: {title[:40]} ({conf})")
            mark_raw_event_processed(raw["_id"])
            continue

        severity = detect_severity(title, description)
        
        # Phase 3 — Geo Execution!
        # Step 1: SpaCy NER extraction mapping
        locations = extract_locations(f"{title}. {description}")
        resolved_coords = None
        
        # Step 2: Extract & Verify standardizations across candidates
        for raw_loc in locations:
            # Map aliases globally
            norm_loc = normalize_location(raw_loc)
            
            # Step 3: Run against MongoDB Cache -> Nominatim Geopy Layer natively
            res = resolve_location(norm_loc)
            
            if res:
                resolved_coords = {
                    "name": norm_loc,  # Keep original casing, don't force title case
                    "state": "Unknown", 
                    "country": "India", 
                    "lat": res[0], "lon": res[1], 
                    "formatted": res[2]
                }
                break
                
        # Skip event if no valid location found (don't create fake geo data)
        if not resolved_coords:
            logger.info(f"[Pipeline] Skipping event with no valid location: {title[:40]}")
            mark_raw_event_processed(raw["_id"])
            continue
            
        # Step 4: Validate natively against $near spatial duplication system immediately
        merged_target = deduplicate_spatial(
            disaster_type=dtype,
            lat=resolved_coords["lat"],
            lon=resolved_coords["lon"],
            confidence=conf,
            radius_km=DEDUP_RADIUS_KM,
            hours=DEDUP_TIME_WINDOW
        )
        
        # Stop pushing into the processed queue entirely if it merged locally into an existing one
        if not merged_target:
            processed_event = {
                "raw_event_id": raw["_id"],
                "disaster_type": dtype,
                "severity": severity,
                "confidence": conf,
                "source": raw.get("source", "Unknown"),
                "source_count": 1,  # Initialize source count
                "source_reliability": 0.80,  # Default reliability
                "is_active": True,  # Mark as active
                "timestamp": raw.get("timestamp"),
                "created_at": datetime.now(),
                "location": {
                    "name": resolved_coords["name"],
                    "state": resolved_coords["state"],
                    "country": resolved_coords["country"],
                    "geo": {
                        "type": "Point",
                        "coordinates": [resolved_coords["lon"], resolved_coords["lat"]] 
                    }
                }
            }
            
            insert_processed_event(processed_event)
            
        mark_raw_event_processed(raw["_id"])
        processed_count += 1
            
    # Phase 3 Step 5: Process clustering mechanisms over active bubbles
    run_clustering()
    
    # Phase 4 Step 6: Alert Triggering Engine evaluation
    alerts_fired = check_and_generate_alerts()
    if alerts_fired > 0:
        logger.warning(f"[Pipeline] ALERT ENGINE: Fired {alerts_fired} new extreme priority alerts this cycle!")
    
    logger.info(f"[Pipeline] Cycle complete. Successfully deployed {processed_count}/{len(raw_events)} events.")
    return processed_count
