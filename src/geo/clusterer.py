"""
src/geo/clusterer.py
────────────────────
Applies DBSCAN unsupervised machine learning exclusively
to group 'processed_events' into massive regional crisis bubbles.
Runs routinely in the background POST-processing.
"""

import logging
from collections import defaultdict
from typing import Any

import numpy as np
from sklearn.cluster import DBSCAN

from src.db.crud import _col, get_processed_events

logger = logging.getLogger(__name__)


def run_clustering(hours: int = 48, eps_km: float = 100.0) -> int:
    """
    Execute DBSCAN against all active processed_events in the database
    to group connected crisis zones via a distinct 'cluster_id'.
    """
    
    # Extract only strictly active elements in the radius
    events = get_processed_events(hours=hours, limit=5000)
    
    if len(events) < 2:
        logger.debug("[Clusterer] Not enough active events to perform clustering.")
        return 0
        
    # We must collect exactly coordinate arrays (lat/lon)
    coords = []
    valid_events = []
    
    for ev in events:
        try:
            # db returns geojson format standard: [lon, lat]
            lon, lat = ev["location"]["geo"]["coordinates"]
            coords.append([lat, lon]) # Scikit requires [lat, lon] usually for haversine
            valid_events.append(ev)
        except KeyError:
            pass
            
    if len(valid_events) < 2:
        return 0
        
    # Initialize radian conversions for Haversine distances
    X = np.radians(coords)
    kms_per_radian = 6371.0088
    eps_in_radians = eps_km / kms_per_radian
    
    # DBSCAN 
    db = DBSCAN(eps=eps_in_radians, min_samples=2, algorithm='ball_tree', metric='haversine')
    db.fit(X)
    
    labels = db.labels_
    
    updates_made = 0
    grouped = defaultdict(list)
    
    for label, event in zip(labels, valid_events):
        if label != -1:  # -1 signifies unclustered noise naturally
            grouped[label].append(event)
            
    # Commit changes uniquely back to MongoDB using a single loop
    for cluster_label, clustered_events in grouped.items():
        base_id = str(clustered_events[0]["_id"])[:8]
        cluster_assignment_id = f"CL-{base_id}"
        
        for ev in clustered_events:
            if ev.get("cluster_id") != cluster_assignment_id:
                _col("processed_events").update_one(
                    {"_id": ev["_id"]},
                    {"$set": {"cluster_id": cluster_assignment_id}}
                )
                updates_made += 1
                
    logger.info(f"[Clusterer] Executed across {len(valid_events)} nodes. Grouped into {len(grouped)} structural clusters. DB Updates: {updates_made}.")
    return len(grouped)
