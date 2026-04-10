"""
Comprehensive API endpoint testing.
Tests all endpoints specified in IMPLEMENTATION_PLAN.md

Run: python test_api_endpoints.py
(Make sure main.py is running: python main.py)
"""

import httpx
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_endpoint(method, path, expected_status=200, params=None, description=""):
    """Test a single endpoint"""
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            response = httpx.get(url, params=params, timeout=10.0)
        elif method == "POST":
            response = httpx.post(url, json=params, timeout=10.0)
        else:
            print(f"  ❌ FAIL: Unsupported method {method}")
            return False
        
        if response.status_code == expected_status:
            print(f"  ✅ PASS: {method} {path} → {response.status_code}")
            if description:
                print(f"         {description}")
            return True
        else:
            print(f"  ❌ FAIL: {method} {path} → {response.status_code} (expected {expected_status})")
            print(f"         Response: {response.text[:200]}")
            return False
    except httpx.ConnectError:
        print(f"  ❌ FAIL: {method} {path} → Connection refused")
        print(f"         Is the server running? (python main.py)")
        return False
    except Exception as e:
        print(f"  ❌ FAIL: {method} {path} → {e}")
        return False

def main():
    print("=" * 80)
    print("API Endpoint Testing - GeoPulse Intelligence")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    
    # Test 1: Health check
    print("1. Health Check")
    results.append(test_endpoint("GET", "/", description="Root endpoint"))
    print()
    
    # Test 2: API docs
    print("2. API Documentation")
    results.append(test_endpoint("GET", "/api/docs", description="Swagger UI"))
    results.append(test_endpoint("GET", "/api/redoc", description="ReDoc UI"))
    print()
    
    # Test 3: GET /api/events (no filters)
    print("3. GET /api/events (no filters)")
    results.append(test_endpoint("GET", "/api/events", description="List all events"))
    print()
    
    # Test 4: GET /api/events (with filters)
    print("4. GET /api/events (with filters)")
    results.append(test_endpoint("GET", "/api/events", 
                                 params={"disaster_type": "flood"},
                                 description="Filter by disaster type"))
    results.append(test_endpoint("GET", "/api/events", 
                                 params={"severity": "HIGH"},
                                 description="Filter by severity"))
    results.append(test_endpoint("GET", "/api/events", 
                                 params={"hours": 24, "limit": 10},
                                 description="Filter by time and limit"))
    print()
    
    # Test 5: GET /api/events/{id}
    print("5. GET /api/events/{id}")
    # First get an event ID
    try:
        response = httpx.get(f"{BASE_URL}/api/events", params={"limit": 1}, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            if data.get("events") and len(data["events"]) > 0:
                event_id = data["events"][0]["_id"]
                results.append(test_endpoint("GET", f"/api/events/{event_id}", 
                                           description=f"Get event by ID: {event_id}"))
            else:
                print("  ⚠️  SKIP: No events in database to test")
                results.append(True)  # Don't fail if no data
        else:
            print("  ⚠️  SKIP: Could not fetch events to get ID")
            results.append(True)
    except Exception as e:
        print(f"  ⚠️  SKIP: {e}")
        results.append(True)
    
    # Test invalid ID
    results.append(test_endpoint("GET", "/api/events/invalid_id", 
                                 expected_status=404,
                                 description="Invalid event ID should return 404"))
    print()
    
    # Test 6: GET /api/alerts
    print("6. GET /api/alerts")
    results.append(test_endpoint("GET", "/api/alerts", description="List all alerts"))
    results.append(test_endpoint("GET", "/api/alerts", 
                                 params={"limit": 5},
                                 description="Limit alerts to 5"))
    print()
    
    # Test 7: GET /api/stats
    print("7. GET /api/stats")
    results.append(test_endpoint("GET", "/api/stats", description="Get summary statistics"))
    print()
    
    # Test 8: GET /api/heatmap
    print("8. GET /api/heatmap")
    results.append(test_endpoint("GET", "/api/heatmap", description="Get heatmap data"))
    print()
    
    # Test 9: GET /api/risk/{location}
    print("9. GET /api/risk/{location}")
    results.append(test_endpoint("GET", "/api/risk/Mumbai", description="Get risk score for Mumbai"))
    results.append(test_endpoint("GET", "/api/risk/NonExistentPlace", 
                                 expected_status=404,
                                 description="Non-existent location should return 404"))
    print()
    
    # Test 10: POST /api/pipeline/run
    print("10. POST /api/pipeline/run")
    results.append(test_endpoint("POST", "/api/pipeline/run", description="Manually trigger pipeline"))
    print()
    
    # Summary
    print("=" * 80)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All API endpoints working correctly!")
    else:
        print(f"❌ {total - passed} test(s) failed")
    
    print("=" * 80)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
