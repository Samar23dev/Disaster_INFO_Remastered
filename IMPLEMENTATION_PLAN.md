# 🚨 GeoPulse Intelligence — Disaster Information System
## Implementation Plan (v2 — MongoDB Edition)

> **Type:** Research Project  
> **Stack:** Python · FastAPI · Streamlit · MongoDB · spaCy · HuggingFace · Gemini  
> **Scope:** Local development → AWS deployment → Future Flutter app  
> **Auth:** Out of scope for now  

---

## 🏗️ Final Architecture

```
Data Sources
  NDMA CAP Feed (XML)
  RSS Feeds (TOI, The Hindu, Indian Express)
  NewsAPI (JSON)
        │
        ▼
  Collection Layer  ──── APScheduler (background cron jobs)
        │
        ▼
  Keyword Pre-filter
        │
        ▼
  MongoDB: raw_events collection
        │
        ▼
  Classification Pipeline
    Rule-Based Classifier  (fast, keyword match)
        │ if confidence < 0.75
    ML Classifier  (distilbart-mnli-12-3, zero-shot)
        │ if confidence < 0.55
    LLM Fallback  (Gemini 1.5 Flash)
        │
        ▼
  Severity Detection
        │
        ▼
  Geo Pipeline
    spaCy NER → Location Normalizer → Nominatim Resolver (cached)
        │
        ▼
  MongoDB $near  ──── Spatial deduplication (50km + 12hr window)
        │
        ▼
  MongoDB: processed_events collection  (with 2dsphere index)
        │
        ▼
  Event Clustering (DBSCAN / $geoWithin)
        │
        ▼
  Alert Engine → MongoDB: alerts collection
        │
        ▼
  FastAPI  ──── REST endpoints (current: Streamlit, future: Flutter)
        │
        ▼
  Streamlit Dashboard
    Home (Live Feed) · Map (Folium) · Analytics · Alerts
```

---

## 🧱 Tech Stack

| Layer | Tool | Why |
|---|---|---|
| Language | Python 3.11 | Ecosystem fit |
| Frontend | Streamlit | Fast research UI |
| API | FastAPI + Uvicorn | Flutter-ready REST API |
| Database | **MongoDB** | Flexible schema, native geo queries |
| Cloud DB | **MongoDB Atlas (free 512MB)** | No EC2 needed for DB |
| ODM/Driver | **pymongo[srv]** | Atlas SRV support |
| Scheduling | APScheduler | Python-native background cron |
| NER | spaCy `en_core_web_sm` | Location extraction |
| ML Model | `valhalla/distilbart-mnli-12-3` | Lighter zero-shot (4× faster than bart-large) |
| LLM Fallback | Gemini 1.5 Flash | Cheap + fast, capped at 10 calls/cycle |
| Geo API | OSM Nominatim | Free, no key needed |
| News | NewsAPI (newsapi.org) | 100 req/day free, structured JSON |
| RSS | feedparser | Standard XML RSS parsing |
| Maps | folium + streamlit-folium | Interactive maps in Streamlit |
| Clustering | scikit-learn DBSCAN | Spatial event grouping |
| HTTP | httpx | Async-compatible |
| XML | lxml | NDMA CAP parsing |

---

## 📁 Project Structure

```
DisasterManagement/
│
├── main.py                         # Unified entry: FastAPI + APScheduler
├── app.py                          # Streamlit dashboard entry
├── IMPLEMENTATION_PLAN.md          # This file
├── README.md
├── pyproject.toml
├── requirements.txt
├── .env                            # Keys (not committed to git)
├── .env.example                    # Template for .env
├── .gitignore
│
├── src/
│   ├── __init__.py
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py             # MongoDB connection + index init
│   │   └── crud.py                 # All read/write operations
│   │
│   ├── collectors/                 # PHASE 1 — Data Collection
│   │   ├── __init__.py
│   │   ├── ndma_collector.py       # NDMA CAP XML feed
│   │   ├── rss_collector.py        # TOI / Hindu / Express RSS feeds
│   │   └── newsapi_collector.py    # NewsAPI JSON feed
│   │
│   ├── processors/                 # PHASE 1 — Pre-processing
│   │   ├── __init__.py
│   │   ├── keyword_filter.py       # Disaster keyword pre-filter
│   │   ├── normalizer.py           # All sources → common schema
│   │   └── deduplicator.py         # SHA256 hash dedup before insert
│   │
│   ├── classifiers/                # PHASE 2 — Classification
│   │   ├── __init__.py
│   │   ├── rule_classifier.py      # Keyword-based (fast path)
│   │   ├── ml_classifier.py        # HuggingFace zero-shot (singleton)
│   │   ├── llm_fallback.py         # Gemini API (last resort)
│   │   ├── severity_detector.py    # HIGH / MEDIUM / LOW rules
│   │   └── pipeline.py             # Orchestrates the full chain
│   │
│   ├── geo/                        # PHASE 3 — Geo Intelligence
│   │   ├── __init__.py
│   │   ├── ner_extractor.py        # spaCy GPE extraction
│   │   ├── loc_normalizer.py       # Bombay→Mumbai alias dict
│   │   ├── geo_resolver.py         # Nominatim + geo_cache collection
│   │   ├── spatial_dedup.py        # MongoDB $near dedup (50km/12hr)
│   │   └── clusterer.py            # DBSCAN cluster assignment
│   │
│   ├── alerts/                     # PHASE 4 — Alert Engine
│   │   ├── __init__.py
│   │   ├── alert_engine.py         # Trigger rules → write alerts
│   │   ├── risk_scorer.py          # Location risk score
│   │   └── safety_advisor.py       # Gemini safety tips (cached)
│   │
│   ├── api/                        # FastAPI — Flutter-ready REST
│   │   ├── __init__.py
│   │   ├── app.py                  # FastAPI instance
│   │   └── routes/
│   │       ├── events.py           # GET /api/events
│   │       ├── alerts.py           # GET /api/alerts
│   │       └── stats.py            # GET /api/stats, /api/heatmap
│   │
│   └── scheduler/
│       ├── __init__.py
│       └── jobs.py                 # APScheduler job definitions
│
└── dashboard/                      # Streamlit UI
    ├── pages/
    │   ├── 1_Home.py               # Live event feed + cards
    │   ├── 2_Map.py                # Folium map + clusters
    │   ├── 3_Analytics.py          # Charts + state breakdown
    │   └── 4_Alerts.py             # Alert history + risk scores
    └── components/
        ├── event_card.py
        ├── sidebar.py
        └── map_builder.py
```

---

## 🗃️ MongoDB Collections & Schemas

### Connection
```
Local Dev (MongoDB Compass):  mongodb://localhost:27017/disaster_db
Future Prod (Atlas):          mongodb+srv://<user>:<pass>@<cluster>.mongodb.net/disaster_db
```
> **Phase 0 uses MongoDB Compass (local).** Install MongoDB Community Server + Compass GUI.
> When ready to deploy, just change `MONGO_URI` in `.env` — zero code change.

**Compass setup:**
- Download: https://www.mongodb.com/try/download/compass
- Connect to: `mongodb://localhost:27017`
- Database name: `disaster_db`
- You can inspect all collections live as data flows in

---

### Collection: `raw_events`
```json
{
  "_id": "ObjectId (auto)",
  "source": "NDMA | TOI | TheHindu | IndianExpress | NewsAPI",
  "title": "Flood warning issued for Assam",
  "description": "Heavy rainfall expected...",
  "link": "https://...",
  "timestamp": "ISODate",
  "raw_content": "original XML or JSON string",
  "dedup_hash": "sha256(source+title[:50]+date_hour)",
  "is_processed": false,
  "created_at": "ISODate"
}
```

**Indexes:**
```python
collection.create_index("dedup_hash", unique=True)   # prevents duplicates
collection.create_index("is_processed")              # fast unprocessed fetch
collection.create_index("created_at")                # time-based queries
```

---

### Collection: `processed_events`
```json
{
  "_id": "ObjectId (auto)",
  "raw_event_id": "ObjectId",
  "disaster_type": "flood | earthquake | cyclone | landslide | heatwave | fire | tsunami | storm",
  "location": {
    "name": "Guwahati",
    "state": "Assam",
    "country": "India",
    "geo": {
      "type": "Point",
      "coordinates": [91.7362, 26.1445]
    }
  },
  "severity": "HIGH | MEDIUM | LOW",
  "confidence": 0.87,
  "source": "NDMA",
  "source_reliability": 0.95,
  "source_count": 3,
  "cluster_id": "cluster_042",
  "is_active": true,
  "timestamp": "ISODate",
  "created_at": "ISODate"
}
```

**Indexes:**
```python
# 2dsphere REQUIRED for all geo queries
collection.create_index([("location.geo", "2dsphere")])
collection.create_index("disaster_type")
collection.create_index("severity")
collection.create_index("is_active")
collection.create_index("timestamp")
```

> ⚠️ GeoJSON format uses [longitude, latitude] — opposite of (lat, lon).
> Always store as coordinates: [lon, lat]

---

### Collection: `alerts`
```json
{
  "_id": "ObjectId (auto)",
  "event_id": "ObjectId",
  "severity": "HIGH | MEDIUM | LOW",
  "message": "⚠️ Flood Alert — Guwahati, Assam",
  "safety_tips": [
    "Move to higher ground immediately",
    "Avoid electrical equipment",
    "Call 112 for emergency services"
  ],
  "is_read": false,
  "created_at": "ISODate"
}
```

---

### Collection: `geo_cache`
```json
{
  "_id": "guwahati assam india",
  "lat": 26.1445,
  "lon": 91.7362,
  "display_name": "Guwahati, Assam, India",
  "cached_at": "ISODate"
}
```
> Using the query string as `_id` makes lookups O(1) with no extra index.

---

## ⏱️ Scheduler — Cron Jobs (APScheduler)

```
main.py starts
  │
  ├── FastAPI server (uvicorn) → port 8000
  └── APScheduler (BackgroundScheduler)
        │
        ├── Job 1: run_ndma_collection     → every 3 minutes
        ├── Job 2: run_rss_collection      → every 8 minutes
        ├── Job 3: run_newsapi_collection  → every 15 minutes
        └── Job 4: run_full_pipeline       → every 10 minutes
              (classification → geo → dedup → clustering → alerts)
```

```python
# src/scheduler/jobs.py
scheduler = BackgroundScheduler()
scheduler.add_job(run_ndma_collection,   'interval', minutes=3)
scheduler.add_job(run_rss_collection,    'interval', minutes=8)
scheduler.add_job(run_newsapi_collection,'interval', minutes=15)
scheduler.add_job(run_full_pipeline,     'interval', minutes=10)
scheduler.start()
```

---

## 🔄 Full Pipeline Flow

```
COLLECTION (every 3–15 min per source)
  HTTP GET → parse XML/JSON → keyword_filter → normalize → dedup_hash check → insert raw_events

PROCESSING (every 10 min)
  Fetch raw_events where is_processed = False
    │
    For each event:
    │
    ├── Rule Classifier       → conf > 0.75? → use it
    ├── ML Classifier         → conf > 0.55? → use it  
    └── Gemini Fallback       → always returns result (max 10/cycle)
    │
    ├── Severity Detector     → HIGH / MEDIUM / LOW
    ├── spaCy NER             → extract city, state
    ├── Alias Normalizer      → Bombay → Mumbai
    ├── Nominatim Resolver    → check geo_cache → query API → cache result
    ├── Spatial Dedup ($near) → within 50km + 12hr? → merge, skip insert
    └── Insert processed_events (with GeoJSON coordinates)
    │
    Mark raw_event is_processed = True

POST-PROCESSING
  DBSCAN clustering → assign cluster_id to recent events
  Alert Engine      → check triggers → write alerts
```

---

## 🌐 Data Sources

| Source | Type | Interval | Free? | Key Needed? |
|---|---|---|---|---|
| NDMA CAP | XML/CAP | 3 min | ✅ | ❌ |
| Times of India RSS | XML/RSS | 8 min | ✅ | ❌ |
| The Hindu RSS | XML/RSS | 8 min | ✅ | ❌ |
| Indian Express RSS | XML/RSS | 8 min | ✅ | ❌ |
| NewsAPI | JSON | 15 min | ✅ (100/day) | ✅ `NEWS_API_KEY` |

### Source Reliability Weights
| Source | Weight |
|---|---|
| NDMA | 0.95 |
| NewsAPI | 0.80 |
| RSS | 0.70 |

Used in confidence scoring: `final_confidence = model_score * source_weight`

---

## 🤖 Classification Pipeline

```
Input: title + description text
  │
  ├─ STEP 1: Rule Classifier (< 1ms)
  │     Keywords: ["flood","earthquake","cyclone","landslide",
  │                "heatwave","fire","tsunami","storm","cloudburst"]
  │     If match → label + confidence=0.75
  │     If conf > 0.75 → DONE ✓
  │
  ├─ STEP 2: ML Classifier (~500ms first run, ~50ms cached)
  │     Model: valhalla/distilbart-mnli-12-3
  │     Zero-shot classification against disaster labels
  │     Returns top label + score
  │     If score > 0.55 → DONE ✓
  │
  └─ STEP 3: Gemini 1.5 Flash Fallback (~1-2s)
        Only when confidence < 0.55 or no rule match
        Hard cap: 10 calls per pipeline cycle
        Returns: { disaster_type, confidence, reasoning }
```

### Severity Detection Rules
```
HIGH   → "killed", "dead", "deaths", "destroyed", "evacuat", "rescue", "collapse"
MEDIUM → "warning", "alert", "watch", "expected", "possible", "risk"
LOW    → "update", "monitoring", "advisory", "normal"
```

---

## 📍 Geo Pipeline (Phase 3)

### Why MongoDB Replaces Most Geo Code

**SQLite approach** — Haversine math in Python, DBSCAN manually:
```python
# 50+ lines of manual distance calculation
def haversine(lat1, lon1, lat2, lon2): ...
for event in all_events:
    if haversine(...) < 50: merge(event)
```

**MongoDB approach** — One query:
```python
db.processed_events.find({
    "disaster_type": disaster_type,
    "location.geo": {
        "$near": {
            "$geometry": {"type": "Point", "coordinates": [lon, lat]},
            "$maxDistance": 50000   # 50km
        }
    },
    "timestamp": {"$gte": cutoff_12hr}
})
```

### Geo-Resolution Flow
```
Raw text: "Flood in Guwahati, Assam"
    │
    spaCy NER → ["Guwahati", "Assam"]
    │
    Alias check → no change (not an alias)
    │
    geo_cache lookup → "guwahati assam india"
      → Hit?  Return cached [91.7362, 26.1445]
      → Miss? Query Nominatim → sleep(1.1s) → cache → return
    │
    Store as GeoJSON:
    { "type": "Point", "coordinates": [91.7362, 26.1445] }
```

---

## 🚨 Alert Engine (Phase 4)

### Trigger Rules
```python
if severity == "HIGH":                          → always alert
if severity == "MEDIUM" and source_count >= 3:  → alert
if confidence >= 0.85:                          → alert
```

### Risk Scoring per Location
```
risk_score = (events_24h * 0.5) + (avg_severity_score * 0.3) + (source_count * 0.2)
→ 0-1.5 = LOW
→ 1.5-3  = MEDIUM
→ 3-5    = HIGH
→ 5+     = CRITICAL
```

### Safety Tips (Gemini — cached per disaster type)
```python
prompt = f"Disaster: {type}. Give exactly 5 safety steps as JSON array."
# Cached in memory per type — Gemini not called twice for same type
```

---

## 🌍 FastAPI Endpoints (Flutter-ready)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/events` | List events (filter: type, severity, state) |
| GET | `/api/events/{id}` | Single event detail |
| GET | `/api/alerts` | Recent alerts |
| GET | `/api/stats` | Summary counts + top states |
| GET | `/api/heatmap` | Coordinates + weights for map |
| GET | `/api/risk/{location}` | Risk score for a location |
| POST | `/api/pipeline/run` | Manually trigger collection cycle |

---

## 🖥️ Streamlit Dashboard

| Page | Content |
|---|---|
| 1_Home.py | Live feed, event cards, severity badges, auto-refresh |
| 2_Map.py | Folium map, color-coded markers, MarkerCluster, Windy iframe |
| 3_Analytics.py | Disaster type chart, timeline, state breakdown |
| 4_Alerts.py | Alert history, risk score cards, safety tips |

---

## ☁️ AWS Deployment Strategy

### Recommended: EC2 + MongoDB Atlas

```
MongoDB Atlas (free 512MB) ← database, in cloud
        │
EC2 t2.micro (free tier)
  ├── FastAPI (uvicorn, port 8000)
  ├── APScheduler (background jobs)
  └── Streamlit (port 8501)
        │
systemd service → keeps process alive 24/7
```

### systemd service file (`/etc/systemd/system/geopulse.service`)
```ini
[Unit]
Description=GeoPulse Disaster System
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/DisasterManagement
EnvironmentFile=/home/ubuntu/DisasterManagement/.env
ExecStart=/home/ubuntu/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Just change `MONGO_URI` in `.env` from `localhost` to Atlas URI — zero code change.

---

## 📦 Requirements (`requirements.txt`)

```
# API & Server
fastapi
uvicorn[standard]

# Dashboard
streamlit
streamlit-folium
folium

# Database
pymongo[srv]

# Scheduling
apscheduler

# Data Collection
feedparser
httpx
lxml
newsapi-python

# AI / ML
spacy
transformers
torch
google-generativeai

# Geo
geopy

# Clustering
scikit-learn

# Utilities
python-dotenv
```

**Also run:**
```bash
python -m spacy download en_core_web_sm
```

---

## 🔐 Environment Variables (`.env`)

```env
# MongoDB
MONGO_URI=mongodb://localhost:27017      # local dev
# MONGO_URI=mongodb+srv://...           # Atlas (uncomment for prod)
MONGO_DB=disaster_db

# APIs
GEMINI_API_KEY=your_gemini_key_here
NEWS_API_KEY=your_newsapi_key_here

# Settings
LLM_MAX_CALLS_PER_CYCLE=10
ML_CONFIDENCE_THRESHOLD=0.55
RULE_CONFIDENCE_THRESHOLD=0.75
DEDUP_RADIUS_KM=50
DEDUP_TIME_WINDOW_HOURS=12
```

---

## ✅ Phase Execution Checklist

---

### ✅ Phase 0 — Setup & Scaffolding `COMPLETE`

**Project Config**
- [x] `pyproject.toml` — all 32 dependencies declared (uv-compatible, `uv sync` verified)
- [x] `requirements.txt` — human-readable with inline comments
- [x] `.env.example` — committed template with all variables documented
- [x] `.env` — real keys file copied from template (git-ignored)
- [x] `.gitignore` — covers `.env`, `__pycache__`, `.venv`, HuggingFace cache, logs

**Python Package Skeleton** — all `__init__.py` created:
- [x] `src/`, `src/db/`, `src/collectors/`, `src/processors/`
- [x] `src/classifiers/`, `src/geo/`, `src/alerts/`
- [x] `src/api/`, `src/api/routes/`, `src/scheduler/`
- [x] `dashboard/`, `dashboard/pages/`, `dashboard/components/`

**Database Layer**
- [x] `src/db/database.py` — singleton MongoClient, fast-fail ping on startup, all indexes:
  - `raw_events`: `dedup_hash` (unique), `is_processed`, `created_at`
  - `processed_events`: `location.geo` (2dsphere), `disaster_type`, `severity`, `is_active`, `timestamp`
  - `alerts`: `event_id`, `created_at`, `is_read`
  - `geo_cache`: `cached_at`
- [x] `src/db/crud.py` — complete CRUD layer (nothing else talks to MongoDB directly):
  - `insert_raw_event()` — dedup-safe, catches E11000 silently
  - `get_unprocessed_events(limit)` — oldest-first batch fetch
  - `mark_raw_event_processed(id)`
  - `insert_processed_event()` — GeoJSON-aware
  - `find_nearby_event()` — MongoDB `$near` spatial dedup (50km / 12hr)
  - `increment_source_count()` — merge duplicate geo events
  - `get_processed_events()` — filterable by type / severity / state / hours
  - `get_event_by_id()`, `get_stats()` (aggregation pipeline)
  - `insert_alert()`, `get_recent_alerts()`, `mark_alert_read()`
  - `get_geo_cache()`, `set_geo_cache()` — Nominatim cache with upsert

**Scheduler Skeleton**
- [x] `src/scheduler/jobs.py` — APScheduler BackgroundScheduler (IST timezone):
  - Job 1: NDMA collector → every 3 min
  - Job 2: RSS collector → every 8 min
  - Job 3: NewsAPI collector → every 15 min
  - Job 4: Full pipeline → every 10 min
  - Lazy imports on each job (avoids circular import errors)

**FastAPI Skeleton**
- [x] `src/api/app.py` — factory with CORS, docs at `/api/docs`
- [x] `src/api/routes/events.py` — `GET /api/events` (filters: type/severity/state/hours) + `GET /api/events/{id}`
- [x] `src/api/routes/alerts.py` — `GET /api/alerts`
- [x] `src/api/routes/stats.py` — `GET /api/stats` + `GET /api/heatmap`

**Entry Points**
- [x] `main.py` — ordered startup: DB init → scheduler → uvicorn (FastAPI)
- [x] `app.py` — Streamlit placeholder entry, confirms Phase 0 complete

**Dependencies**
- [x] 148 packages installed via `uv sync` (Python 3.13.12, `.venv/`)
- [x] `en_core_web_sm` v3.8.0 downloaded via `uv run python -m spacy download en_core_web_sm`

> ⚠️ **Action required:** Add your real `GEMINI_API_KEY` and `NEWS_API_KEY` to `.env`
> ⚠️ **Action required:** Make sure MongoDB Community Server is running — verify in Compass
> 🗑️ **Cleanup:** Delete `requirments.txt` (typo leftover from project init)

---

### 🔲 Phase 1 — Data Collection `NEXT`

- [ ] `src/processors/keyword_filter.py` — disaster keyword pre-filter
- [ ] `src/processors/normalizer.py` — all sources → common schema dict
- [ ] `src/processors/deduplicator.py` — `make_dedup_hash()` utility
- [ ] `src/collectors/ndma_collector.py` — NDMA CAP XML, ETag caching
- [ ] `src/collectors/rss_collector.py` — TOI / The Hindu / Indian Express
- [ ] `src/collectors/newsapi_collector.py` — NewsAPI.org JSON
- [ ] **Test:** Run collectors manually → check `raw_events` in Compass

---

### 🔲 Phase 2 — Classification

- [ ] `src/classifiers/rule_classifier.py` — keyword fast-path
- [ ] `src/classifiers/ml_classifier.py` — `distilbart-mnli-12-3` singleton
- [ ] `src/classifiers/llm_fallback.py` — Gemini 1.5 Flash (max 10/cycle)
- [ ] `src/classifiers/severity_detector.py` — HIGH / MEDIUM / LOW rules
- [ ] `src/classifiers/pipeline.py` — full rule → ML → LLM chain
- [ ] **Test:** 10 raw events → verify `processed_events` in Compass

---

### 🔲 Phase 3 — Geo + Clustering

- [ ] `src/geo/ner_extractor.py` — spaCy GPE extraction
- [ ] `src/geo/loc_normalizer.py` — alias dict (Bombay → Mumbai etc.)
- [ ] `src/geo/geo_resolver.py` — Nominatim + `geo_cache` collection
- [ ] `src/geo/spatial_dedup.py` — MongoDB `$near` dedup
- [ ] `src/geo/clusterer.py` — DBSCAN cluster assignment
- [ ] **Test:** Events get lat/lon + cluster_id, check Compass map view

---

### 🔲 Phase 4 — Alerts + Intelligence

- [ ] `src/alerts/alert_engine.py` — trigger rules → alerts collection
- [ ] `src/alerts/risk_scorer.py` — location risk score
- [ ] `src/alerts/safety_advisor.py` — Gemini tips, cached per type
- [ ] **Test:** HIGH severity event → alert document visible in Compass

---

### 🔲 Streamlit Dashboard

- [ ] `dashboard/pages/1_Home.py` — live feed, severity cards, auto-refresh
- [ ] `dashboard/pages/2_Map.py` — Folium + clusters + Windy iframe
- [ ] `dashboard/pages/3_Analytics.py` — charts, breakdown by type/state
- [ ] `dashboard/pages/4_Alerts.py` — alert history, risk score cards
- [ ] `dashboard/components/event_card.py`
- [ ] `dashboard/components/sidebar.py`
- [ ] `dashboard/components/map_builder.py`

---

### 🔲 Integration & Polish

- [ ] End-to-end test: collection → classification → map marker visible
- [ ] Mock data fallback (for when feeds are offline)
- [ ] `README.md` — setup instructions + architecture diagram
- [ ] Commit + push Phase 0 to GitHub

---

## 🔥 Known Risks & Mitigations

| Risk | Mitigation |
|---|---|
| NDMA feed down / URL changes | try/except, skip cycle, log warning, mock fallback |
| Nominatim rate limit (1 req/s) | geo_cache collection, sleep(1.1s) |
| HuggingFace slow first load | Load at startup as singleton |
| Gemini API cost overrun | Hard cap 10 calls/cycle, cache safety tips by type |
| NewsAPI 100/day limit | 15-min interval = 96 req/day (just within limit) |
| MongoDB write concurrency | pymongo handles this natively |
| GeoJSON lon/lat order confusion | Always store as [lon, lat], documented in crud.py |

---

*Last updated: Phase 0 complete ✅ — Phase 1 is next*

