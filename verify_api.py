"""
Quick API verification - checks all routes are registered correctly.
Run: python verify_api.py
"""

from src.api.app import create_app

app = create_app()

print("=" * 70)
print("API Route Verification")
print("=" * 70)

# Get all routes
routes = []
for route in app.routes:
    if hasattr(route, 'methods') and hasattr(route, 'path'):
        for method in route.methods:
            if method != "HEAD":  # Skip HEAD methods
                routes.append((method, route.path))

# Sort by path
routes.sort(key=lambda x: x[1])

print(f"\nTotal routes: {len(routes)}\n")

# Expected routes from IMPLEMENTATION_PLAN.md
expected_routes = [
    ("GET", "/"),
    ("GET", "/api/events"),
    ("GET", "/api/events/{event_id}"),
    ("GET", "/api/alerts"),
    ("GET", "/api/stats"),
    ("GET", "/api/heatmap"),
    ("GET", "/api/risk/{location}"),
    ("POST", "/api/pipeline/run"),
]

print("Registered Routes:")
print("-" * 70)
for method, path in routes:
    status = "✅" if (method, path) in expected_routes else "ℹ️ "
    print(f"{status} {method:6} {path}")

print("\n" + "=" * 70)
print("Expected Routes Check:")
print("-" * 70)

all_found = True
for method, path in expected_routes:
    if (method, path) in routes:
        print(f"✅ {method:6} {path}")
    else:
        print(f"❌ {method:6} {path} - MISSING!")
        all_found = False

print("\n" + "=" * 70)
if all_found:
    print("✅ All expected routes are registered!")
else:
    print("❌ Some routes are missing!")
print("=" * 70)
