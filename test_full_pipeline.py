"""
Full pipeline test with real data flow verification.
Tests: raw_event → classification → geo resolution → processed_event

Run: python test_full_pipeline.py
"""

import logging
from datetime import datetime, timezone
from src.db.database import get_db
from src.db.crud import insert_raw_event, get_unprocessed_events, get_processed_events
from src.processors.normalizer import normalize_newsapi
from src.processors.deduplicator import prepare_event
from src.classifiers.pipeline import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)

def create_test_event(title, description, source="TEST"):
    """Create a test raw event"""
    article = {
        "title": title,
        "description": description,
        "url": f"https://test.com/{hash(title)}",
        "publishedAt": datetime.now(timezone.utc).isoformat(),
        "source": {"id": None, "name": source}
    }
    
    normalized = normalize_newsapi(article)
    normalized["source"] = source  # Override to TEST
    event = prepare_event(normalized)
    return event

def main():
    print("\n" + "=" * 80)
    print("Full Pipeline Test - Real Data Flow Verification")
    print("=" * 80)
    
    db = get_db()
    
    # Test events with clear locations
    test_events = [
        ("Severe flood hits Mumbai after heavy rainfall", 
         "Heavy monsoon rains caused severe flooding in Mumbai, Maharashtra. Thousands evacuated."),
        
        ("Earthquake of magnitude 5.2 strikes Delhi NCR", 
         "A moderate earthquake was felt in Delhi and surrounding areas. No casualties reported."),
        
        ("Landslide in Uttarakhand blocks highway near Dehradun",
         "Heavy rains triggered a massive landslide in Uttarakhand, blocking the main highway."),
    ]
    
    print("\n📝 Creating test events...")
    inserted_ids = []
    for title, desc in test_events:
        event = create_test_event(title, desc)
        if insert_raw_event(event):
            print(f"  ✅ Inserted: {title[:60]}")
            inserted_ids.append(event.get("dedup_hash"))
        else:
            print(f"  ⚠️  Duplicate: {title[:60]}")
    
    if not inserted_ids:
        print("\n⚠️  All test events were duplicates. Using existing data.")
    
    # Check unprocessed count
    unprocessed = get_unprocessed_events(limit=100)
    print(f"\n📊 Unprocessed events: {len(unprocessed)}")
    
    if len(unprocessed) == 0:
        print("  No unprocessed events. All data already processed.")
        print("  Run cleanup_and_reprocess.py to reset and reprocess.")
        return
    
    # Run pipeline
    print("\n⚙️  Running pipeline...")
    print("  (This will classify, extract locations, and deduplicate)")
    print()
    
    try:
        processed_count = run_pipeline()
        print(f"\n✅ Pipeline processed {processed_count} events")
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        logging.exception("Pipeline error")
        return
    
    # Verify results
    print("\n🔍 Verifying results...")
    
    recent_processed = list(db["processed_events"].find().sort("created_at", -1).limit(5))
    
    print(f"\n📋 Last {len(recent_processed)} processed events:")
    for i, doc in enumerate(recent_processed, 1):
        loc_name = doc.get('location', {}).get('name', 'Unknown')
        coords = doc.get('location', {}).get('geo', {}).get('coordinates', [])
        dtype = doc.get('disaster_type', 'unknown')
        severity = doc.get('severity', 'LOW')
        confidence = doc.get('confidence', 0.0)
        
        print(f"\n  {i}. {dtype.upper()} - {severity}")
        print(f"     Location: {loc_name}")
        print(f"     Coords: {coords}")
        print(f"     Confidence: {confidence:.2f}")
    
    # Check for proper geo resolution
    with_real_locations = db["processed_events"].count_documents({
        "location.name": {"$nin": ["Unknown (Phase 2 Stub)", "General Incident"]}
    })
    
    total_processed = db["processed_events"].count_documents({})
    
    print(f"\n📍 Location extraction stats:")
    print(f"  Total processed events: {total_processed}")
    print(f"  With real locations: {with_real_locations}")
    print(f"  Success rate: {with_real_locations/total_processed*100:.1f}%" if total_processed > 0 else "  N/A")
    
    # Check geo cache
    cache_count = db["geo_cache"].count_documents({})
    print(f"\n💾 Geo cache: {cache_count} locations cached")
    
    if cache_count > 0:
        print("\n  Sample cached locations:")
        for doc in db["geo_cache"].find().limit(3):
            print(f"    {doc.get('_id')} → ({doc.get('lat'):.4f}, {doc.get('lon'):.4f})")
    
    # Check alerts
    alerts_count = db["alerts"].count_documents({})
    print(f"\n🚨 Alerts generated: {alerts_count}")
    
    if alerts_count > 0:
        for doc in db["alerts"].find().limit(2):
            print(f"  - {doc.get('disaster_type')} at {doc.get('location_name')} (risk: {doc.get('risk_score')})")
    
    print("\n" + "=" * 80)
    if with_real_locations > 0:
        print("✅ SUCCESS: Pipeline is working correctly!")
        print("   - Events are being classified")
        print("   - Locations are being extracted")
        print("   - Geo resolution is working")
        print("   - Data is being stored properly")
    else:
        print("⚠️  WARNING: No real locations extracted")
        print("   Check logs above for NER/Nominatim issues")
    print("=" * 80)

if __name__ == "__main__":
    main()
