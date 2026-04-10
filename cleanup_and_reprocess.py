"""
Cleanup old buggy data and reprocess with fixed Phase 3 code.

This script:
1. Backs up current data (optional)
2. Clears processed_events and alerts (keeps raw_events)
3. Marks all raw_events as unprocessed
4. Runs the pipeline to reprocess with fixed geo resolution
5. Verifies that locations are properly extracted

Run: python cleanup_and_reprocess.py
"""

import logging
from datetime import datetime
from src.db.database import get_db
from src.classifiers.pipeline import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

def main():
    db = get_db()
    
    print("\n" + "=" * 70)
    print("GeoPulse Intelligence - Data Cleanup & Reprocessing")
    print("=" * 70)
    
    # Step 1: Show current state
    print("\n📊 Current Database State:")
    raw_count = db["raw_events"].count_documents({})
    processed_count = db["processed_events"].count_documents({})
    alerts_count = db["alerts"].count_documents({})
    cache_count = db["geo_cache"].count_documents({})
    
    print(f"  raw_events:        {raw_count:>6} documents")
    print(f"  processed_events:  {processed_count:>6} documents")
    print(f"  alerts:            {alerts_count:>6} documents")
    print(f"  geo_cache:         {cache_count:>6} documents")
    
    if raw_count == 0:
        print("\n⚠️  No raw events found. Run collectors first:")
        print("   python -c 'from src.collectors.ndma_collector import run_ndma_collection; run_ndma_collection()'")
        print("   python -c 'from src.collectors.rss_collector import run_rss_collection; run_rss_collection()'")
        return
    
    # Step 2: Confirm cleanup
    print("\n⚠️  This will:")
    print("  1. DELETE all processed_events (old buggy data)")
    print("  2. DELETE all alerts")
    print("  3. KEEP raw_events (source data)")
    print("  4. KEEP geo_cache (location lookups)")
    print("  5. Mark all raw_events as unprocessed")
    print("  6. Re-run pipeline with FIXED Phase 3 code")
    
    response = input("\n❓ Continue? (yes/no): ").strip().lower()
    if response not in ["yes", "y"]:
        print("❌ Cancelled.")
        return
    
    # Step 3: Backup (optional)
    print("\n💾 Creating backup timestamp...")
    backup_time = datetime.now().isoformat()
    print(f"   Backup reference: {backup_time}")
    print("   (MongoDB data not actually backed up - use mongodump if needed)")
    
    # Step 4: Clear old data
    print("\n🗑️  Clearing old processed data...")
    
    result_processed = db["processed_events"].delete_many({})
    print(f"   Deleted {result_processed.deleted_count} processed_events")
    
    result_alerts = db["alerts"].delete_many({})
    print(f"   Deleted {result_alerts.deleted_count} alerts")
    
    # Step 5: Mark all raw events as unprocessed
    print("\n🔄 Marking raw events as unprocessed...")
    result_raw = db["raw_events"].update_many(
        {},
        {"$set": {"is_processed": False}}
    )
    print(f"   Updated {result_raw.modified_count} raw_events")
    
    # Step 6: Run pipeline
    print("\n⚙️  Running pipeline with FIXED Phase 3 code...")
    print("   (This may take a few minutes depending on data volume)")
    print("   (Nominatim rate limit: 1 request per 1.1 seconds)")
    print()
    
    try:
        processed_count = run_pipeline()
        print(f"\n✅ Pipeline complete: {processed_count} events processed")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        print(f"\n❌ Pipeline failed: {e}")
        return
    
    # Step 7: Verify results
    print("\n🔍 Verifying results...")
    
    new_processed = db["processed_events"].count_documents({})
    new_alerts = db["alerts"].count_documents({})
    new_cache = db["geo_cache"].count_documents({})
    
    print(f"  processed_events:  {new_processed:>6} documents")
    print(f"  alerts:            {new_alerts:>6} documents")
    print(f"  geo_cache:         {new_cache:>6} documents")
    
    # Check for proper locations
    print("\n📍 Checking location extraction...")
    
    with_real_locations = db["processed_events"].count_documents({
        "location.name": {"$nin": ["Unknown (Phase 2 Stub)", "General Incident"]}
    })
    
    with_fake_coords = db["processed_events"].count_documents({
        "location.geo.coordinates": [78.9629, 20.5937]  # India center
    })
    
    print(f"  Events with real locations:  {with_real_locations}/{new_processed}")
    print(f"  Events with fake coords:     {with_fake_coords}/{new_processed}")
    
    if with_real_locations > 0:
        print("\n✅ SUCCESS: Locations are being extracted properly!")
        
        # Show sample
        print("\n📋 Sample processed events:")
        for doc in db["processed_events"].find().limit(3):
            loc_name = doc.get('location', {}).get('name', 'Unknown')
            coords = doc.get('location', {}).get('geo', {}).get('coordinates', [])
            print(f"  - {doc.get('disaster_type'):12} | {doc.get('severity'):6} | {loc_name:30} | {coords}")
    else:
        print("\n⚠️  WARNING: No real locations extracted!")
        print("   Possible reasons:")
        print("   1. NER not finding location names in text")
        print("   2. Nominatim failing to resolve locations")
        print("   3. All events skipped due to no valid location")
        print("\n   Check logs above for details.")
    
    if new_cache > 0:
        print(f"\n💾 Geo cache populated with {new_cache} locations")
        print("   (Future lookups will be instant)")
    
    print("\n" + "=" * 70)
    print("Cleanup and reprocessing complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
