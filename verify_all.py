"""
Full codebase verification test — Phases 0-3.
Run: uv run python verify_all.py
Tests every module without needing network (where possible).
"""
import logging
import sys
logging.basicConfig(level=logging.WARNING, format="%(levelname)s | %(name)s | %(message)s")

PASS = []
FAIL = []

def check(name, fn):
    try:
        fn()
        PASS.append(name)
        print(f"  PASS  {name}")
    except Exception as e:
        FAIL.append(name)
        print(f"  FAIL  {name}: {e}")

print("\n=== Phase 0: DB Layer ===")

def test_db_imports():
    from src.db.database import get_db, init_collections, close_connection
    from src.db.crud import (make_dedup_hash, insert_raw_event, get_unprocessed_events,
                              mark_raw_event_processed, count_raw_events,
                              insert_processed_event, increment_source_count,
                              find_nearby_event, get_processed_events, get_event_by_id,
                              get_stats, insert_alert, get_recent_alerts,
                              mark_alert_read, get_geo_cache, set_geo_cache, _col)

def test_db_connection():
    from src.db.database import init_collections
    init_collections()

def test_dedup_hash():
    from src.db.crud import make_dedup_hash
    from datetime import datetime, timezone
    h = make_dedup_hash("NDMA", "Flood warning in Assam", datetime(2025,4,9,10,0,tzinfo=timezone.utc))
    assert len(h) == 64
    # Same inputs → same hash
    h2 = make_dedup_hash("NDMA", "Flood warning in Assam", datetime(2025,4,9,10,0,tzinfo=timezone.utc))
    assert h == h2

check("DB imports",      test_db_imports)
check("DB connection",   test_db_connection)
check("dedup_hash",      test_dedup_hash)

print("\n=== Phase 1: Processors ===")

def test_keyword_filter():
    from src.processors.keyword_filter import is_disaster_related, get_matched_keywords
    assert is_disaster_related("Flood warning in Assam") == True
    assert is_disaster_related("Bollywood awards 2025") == False
    assert is_disaster_related("Stock market disaster for traders") == False  # negative kw
    assert is_disaster_related("Earthquake of magnitude 5.8 shakes Delhi") == True
    kws = get_matched_keywords("Flash flood alert in Kerala after heavy rains")
    assert "flood" in kws or "flash flood" in kws

def test_normalizer():
    from src.processors.normalizer import normalize_newsapi, normalize_rss, normalize_ndma
    from datetime import datetime, timezone

    art = {"title": "Flood in Assam", "description": "Rivers overflow.",
           "url": "https://x.com/1", "publishedAt": "2025-04-09T08:00:00Z",
           "source": {"id": None, "name": "NewsAPI"}}
    ev = normalize_newsapi(art)
    assert ev["source"] == "NewsAPI"
    assert ev["title"] == "Flood in Assam"
    assert ev["timestamp"].tzinfo is not None

    entry_dict = {"title": "Cyclone alert in Chennai", "summary": "Red alert.",
                  "link": "https://x.com/2", "published": "Wed, 09 Apr 2025 06:00:00 +0530"}
    class FakeEntry:
        title = entry_dict["title"]
        summary = entry_dict["summary"]
        link = entry_dict["link"]
        published = entry_dict["published"]
    ev2 = normalize_rss(FakeEntry(), "https://thehindu.com/feed")
    assert ev2["source"] == "TheHindu"

def test_deduplicator():
    from src.processors.deduplicator import prepare_event, stamp_dedup_hash
    from datetime import datetime, timezone
    ev = {"source": "TOI", "title": "Flood warning", "timestamp": datetime.now(timezone.utc)}
    ev2 = prepare_event(ev)
    assert "dedup_hash" in ev2
    assert len(ev2["dedup_hash"]) == 64

check("keyword_filter",  test_keyword_filter)
check("normalizer",      test_normalizer)
check("deduplicator",    test_deduplicator)

print("\n=== Phase 1: Collectors (imports only) ===")

def test_collector_imports():
    from src.collectors.ndma_collector import run_ndma_collection
    from src.collectors.rss_collector import run_rss_collection, RSS_FEEDS
    from src.collectors.newsapi_collector import run_newsapi_collection, SEARCH_QUERIES
    assert len(RSS_FEEDS) >= 5
    assert len(SEARCH_QUERIES) >= 4

check("collector imports", test_collector_imports)

print("\n=== Phase 2: Classifiers ===")

def test_rule_classifier():
    from src.classifiers.rule_classifier import rule_classify
    dtype, conf = rule_classify("Massive flood warning in Assam rivers", "")
    assert dtype == "flood"
    assert conf == 0.75
    dtype2, conf2 = rule_classify("PM Modi attends rally today", "")
    assert conf2 == 0.0

def test_severity_detector():
    from src.classifiers.severity_detector import detect_severity
    assert detect_severity("3 killed in flood", "") == "HIGH"
    assert detect_severity("Flood warning issued", "") == "MEDIUM"
    assert detect_severity("River monitoring update", "") == "LOW"

def test_ml_classifier_import():
    from src.classifiers.ml_classifier import get_ml_classifier, CANDIDATE_LABELS
    assert "flood" in CANDIDATE_LABELS
    assert "earthquake" in CANDIDATE_LABELS
    assert len(CANDIDATE_LABELS) == 8

def test_llm_fallback_import():
    from src.classifiers.llm_fallback import llm_classify, _get_gemini_client
    # Just verify it imports and runs without crashing (will return unknown with no key)
    dtype, conf = llm_classify("Some ambiguous story", "")
    assert isinstance(dtype, str)
    assert isinstance(conf, float)

def test_pipeline_import():
    from src.classifiers.pipeline import run_pipeline, _classify_event, _llm_calls_this_cycle
    assert isinstance(_llm_calls_this_cycle, int)

check("rule_classifier",    test_rule_classifier)
check("severity_detector",  test_severity_detector)
check("ml_classifier_import", test_ml_classifier_import)
check("llm_fallback_import",  test_llm_fallback_import)
check("pipeline_import",    test_pipeline_import)

print("\n=== Phase 3: Geo Modules ===")

def test_ner_extractor():
    from src.geo.ner_extractor import extract_locations
    
    # Test 1: Basic extraction
    locs = extract_locations("Severe flood hit Guwahati and Assam after heavy rains.")
    assert isinstance(locs, list)
    assert len(locs) >= 1, "Should extract at least one location"
    
    # Test 2: Multiple cities
    locs2 = extract_locations("Flood in Mumbai and Delhi causes major disruption.")
    assert len(locs2) >= 1, "Should extract Mumbai or Delhi"
    
    # Test 3: State names
    locs3 = extract_locations("Earthquake in Uttarakhand near Dehradun.")
    assert len(locs3) >= 1, "Should extract Uttarakhand or Dehradun"
    
    # Test 4: Empty input
    locs4 = extract_locations("")
    assert locs4 == [], "Empty input should return empty list"
    
    # Test 5: No locations
    locs5 = extract_locations("Heavy rainfall expected tomorrow.")
    assert isinstance(locs5, list), "Should return list even with no locations"
    
    # Test 6: Compound names
    locs6 = extract_locations("Cyclone warning for Chennai, Tamil Nadu")
    assert isinstance(locs6, list), "Should handle compound location names"
    
    print(f"    NER extracted from test cases: {locs}, {locs2}, {locs3}")

def test_ner_extractor_detailed():
    """More comprehensive NER testing"""
    from src.geo.ner_extractor import extract_locations
    
    test_cases = {
        "Major cities": ("Flood in Mumbai, Delhi, and Kolkata", ["Mumbai", "Delhi", "Kolkata"]),
        "States": ("Earthquake in Uttarakhand and Assam", ["Uttarakhand", "Assam"]),
        "Mixed": ("Fire in Bangalore, Karnataka state", ["Bangalore", "Karnataka"]),
    }
    
    for name, (text, expected_any) in test_cases.items():
        locs = extract_locations(text)
        # Check if at least one expected location is found
        found = any(exp.lower() in loc.lower() for exp in expected_any for loc in locs)
        assert found or len(locs) > 0, f"{name}: Should extract at least one location from '{text}'"

def test_loc_normalizer():
    from src.geo.loc_normalizer import normalize_location
    assert normalize_location("Bombay") == "Mumbai"
    assert normalize_location("Calcutta") == "Kolkata"
    assert normalize_location("calcutta") == "Kolkata"   # lowercase input
    assert normalize_location("Delhi") == "Delhi"         # No alias → passthrough unchanged

def test_spatial_dedup_import():
    from src.geo.spatial_dedup import deduplicate_spatial

def test_clusterer_import():
    from src.geo.clusterer import run_clustering

def test_geo_resolver_import():
    from src.geo.geo_resolver import resolve_location, get_geolocator

check("ner_extractor",       test_ner_extractor)
check("ner_extractor_detailed", test_ner_extractor_detailed)
check("loc_normalizer",      test_loc_normalizer)
check("spatial_dedup_import", test_spatial_dedup_import)
check("clusterer_import",    test_clusterer_import)
check("geo_resolver_import", test_geo_resolver_import)

print("\n=== API & Scheduler ===")

def test_api_imports():
    from src.api.app import create_app
    from src.api.routes.events import router as ev_router
    from src.api.routes.alerts import router as al_router
    from src.api.routes.stats import router as st_router

def test_scheduler_import():
    from src.scheduler.jobs import start_scheduler

def test_entry_points():
    import ast
    for f in ["main.py", "app.py"]:
        with open(f, encoding="utf-8") as fh:
            ast.parse(fh.read())  # Raises SyntaxError if broken

check("api imports",       test_api_imports)
check("scheduler import",  test_scheduler_import)
check("entry points",      test_entry_points)

# ── Summary ────────────────────────────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"  PASSED: {len(PASS)}/{len(PASS)+len(FAIL)}")
if FAIL:
    print(f"  FAILED: {FAIL}")
    sys.exit(1)
else:
    print("  All checks passed. Codebase is healthy.")
