# 🚨 GeoPulse Intelligence — Disaster Information System
## Implementation Plan (v3 — Verified & Updated)

> **Type:** Research Project
> **Stack:** Python · FastAPI · Streamlit · MongoDB · spaCy · HuggingFace · Gemini
> **Scope:** Local development → AWS deployment → Future Flutter app
> **Auth:** Out of scope for now

---

## 🏗️ Final Architecture

```
Data Sources
  NDMA CAP Feed (XML)
  RSS Feeds (TOI, The Hindu, Indian Express, NDTV, Hindustan Times)
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
    LLM Fallback  (Gemini 2.5 Flash)
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
  Event Clustering (DBSCAN / ball_tree haversine)
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
| Language | Python 3.11+ | Ecosystem fit |
| Frontend | Streamlit | Fast research UI |
| API | FastAPI + Uvicorn | Flutter-ready REST API |
| Database | **MongoDB** | Flexible schema, native geo queries |
| Cloud DB | **MongoDB Atlas (free 512MB)** | No EC2 needed for DB |
| ODM/Driver | **pymongo** | Atlas SRV support built-in since v4.x |
| Scheduling | APScheduler | Python-native background cron |
| NER | spaCy `en_core_web_sm` v3.8.0 | Location extraction |
| ML Model | `valhalla/distilbart-mnli-12-3` | Lighter zero-shot (4× faster than bart-large) |
| LLM Fallback | Gemini 2.5 Flash | Cheap + fast, capped at 10 calls/cycle |
| Geo API | OSM Nominatim | Free, no key needed |
| News | NewsAPI (newsapi.org) | 100 req/day free, structured JSON |
| RSS | feedparser | Standard XML RSS parsing |
| Maps | folium + streamlit-folium | Interactive maps in Streamlit |
| Clustering | scikit-learn DBSCAN (ball_tree + haversine) | Spatial event grouping |
| HTTP | httpx | Async-compatible |
| XML | lxml + ElementTree | NDMA CAP parsing |

---

## 📁 Project Structure

```
DisasterManagement/
│
├── main.py                         # Unified entry: FastAPI + APScheduler
├── app.py                          # Streamlit dashboard entry (home page)
├── IMPLEMENTATION_PLAN.md          # This file
├── pyproject.toml                  # uv-compatible, 40+ dependencies
├── requirements.txt                # Human-readable dependency list
├── .env                            # Keys (not committed to git)
├── .env.example                    # Template for .env (9 variables)
├── .gitignore
├── verify_all.py                   # 21/21 module checks
├── verify_api.py                   # API route registration check
├── test_api_endpoints.py           # Live endpoint testing (server must be running)
├── test_full_pipeline.py           # End-to-end data flow test
├── cleanup_and_reprocess.py        # Wipe processed_events + reprocess raw
├── API_VERIFICATION_REPORT.md      # Detailed API test results
│
├── src/
│   ├── __init__.py
│   ├── db/
│   │   ├── database.py             # MongoDB singleton + index init
│   │   └── crud.py                 # All read/write operations (single source of truth)
│   ├── collectors/
│   │   ├── ndma_collector.py       # NDMA CAP XML feed (ETag caching)
│   │   ├── rss_collector.py        # 5 RSS feeds (TOI/Hindu/Express/NDTV/HT)
│   │   └── newsapi_collector.py    # NewsAPI.org JSON (4 search queries)
│   ├── processors/
│   │   ├── keyword_filter.py       # Disaster keyword pre-filter + negative kw exclusion
│   │   ├── normalizer.py           # All sources → common schema dict
│   │   └── deduplicator.py         # SHA256 hash dedup before insert
│   ├── classifiers/
│   │   ├── rule_classifier.py      # Regex keyword fast-path (< 1ms)
│   │   ├── ml_classifier.py        # HuggingFace zero-shot singleton
│   │   ├── llm_fallback.py         # Gemini 2.5 Flash (max 10/cycle)
│   │   ├── severity_detector.py    # HIGH / MEDIUM / LOW rules
│   │   └── pipeline.py             # Full rule → ML → LLM → geo → dedup → alert chain
│   ├── geo/
│   │   ├── ner_extractor.py        # spaCy GPE/LOC extraction (singleton)
│   │   ├── loc_normalizer.py       # Alias dict (Bombay→Mumbai, title-case values)
│   │   ├── geo_resolver.py         # Nominatim + geo_cache, 1.1s rate limit
│   │   ├── spatial_dedup.py        # MongoDB $near dedup (50km / 12hr)
│   │   └── clusterer.py            # DBSCAN cluster assignment (haversine ball_tree)
│   ├── alerts/
│   │   ├── alert_engine.py         # Threshold-based alert generation (risk >= 45)
│   │   ├── risk_scorer.py          # Composite risk score 0-100
│   │   └── safety_advisor.py       # Gemini safety tips (1hr TTL cache per type+severity)
│   ├── api/
│   │   ├── app.py                  # FastAPI factory, CORS, docs at /api/docs
│   │   └── routes/
│   │       ├── events.py           # GET /api/events, GET /api/events/{id}
│   │       ├── alerts.py           # GET /api/alerts
│   │       ├── stats.py            # GET /api/stats, /api/heatmap, /api/risk/{location}
│   │       └── pipeline.py         # POST /api/pipeline/run (BackgroundTasks)
│   └── scheduler/
│       └── jobs.py                 # APScheduler (Asia/Kolkata), lazy imports
│
└── dashboard/                      # Streamlit UI
    ├── app.py                      # Home page (live stats, event breakdown)
    └── components/
        └── sidebar.py              # ⚠️ MISSING — referenced in app.py but not created
    (pages/ directory does not exist yet — Phase 5 incomplete)
```

---

## 🗃️ MongoDB Collections & Schemas

### Connection
```
Local Dev:   mongodb://localhost:27017/disaster_db
Production:  mongodb+srv://<user>:<pass>@<cluster>.mongodb.net/disaster_db
```
> Change `MONGO_URI` in `.env` to switch — zero code change.

### Collection: `raw_events`
```json
{
  "_id": "ObjectId (auto)",
  "source": "NDMA | TOI | TheHindu | IndianExpress | NDTV | HindustanTimes | NewsAPI",
  "title": "Flood warning issued for Assam",
  "description": "Heavy rainfall expected...",
  "link": "https://...",
  "timestamp": "ISODate",
  "raw_content": "original XML or JSON string",
  "dedup_hash": "sha256(source+title[:60]+date_hour)",
  "is_processed": false,
  "created_at": "ISODate"
}
```
**Indexes:** `dedup_hash` (unique), `is_processed`, `created_at`

### Collection: `processed_events`
```json
{
  "_id": "ObjectId (auto)",
  "raw_event_id": "ObjectId",
  "disaster_type": "flood | earthquake | cyclone | landslide | heatwave | fire | tsunami | storm",
  "location": {
    "name": "Guwahati",
    "state": "Unknown",
    "country": "India",
    "geo": { "type": "Point", "coordinates": [91.7362, 26.1445] }
  },
  "severity": "HIGH | MEDIUM | LOW",
  "confidence": 0.87,
  "source": "NDMA",
  "source_reliability": 0.80,
  "source_count": 1,
  "cluster_id": "CL-abc12345",
  "is_active": true,
  "timestamp": "ISODate",
  "created_at": "ISODate"
}
```
**Indexes:** `location.geo` (2dsphere), `disaster_type`, `severity`, `is_active`, `timestamp`

> ⚠️ GeoJSON uses [longitude, latitude] — always store as coordinates: [lon, lat]

### Collection: `alerts`
```json
{
  "_id": "ObjectId (auto)",
  "event_id": "ObjectId",
  "disaster_type": "flood",
  "severity": "HIGH",
  "risk_score": 60,
  "location_name": "Guwahati",
  "cluster_id": "CL-abc12345",
  "safety_advice": "Move to higher ground immediately...",
  "is_read": false,
  "created_at": "ISODate"
}
```
**Indexes:** `event_id`, `created_at`, `is_read`

### Collection: `geo_cache`
```json
{
  "_id": "guwahati, india",
  "lat": 26.1445,
  "lon": 91.7362,
  "display_name": "Guwahati, Assam, India",
  "cached_at": "ISODate"
}
```
> `_id` = query string → O(1) lookup, no extra index needed.

---

## ⏱️ Scheduler — Cron Jobs (APScheduler)

```
main.py starts
  ├── FastAPI server (uvicorn) → port 8000
  └── APScheduler (BackgroundScheduler, Asia/Kolkata timezone)
        ├── Job 1: NDMA CAP Feed Collector     → every 3 minutes
        ├── Job 2: RSS Feed Collector           → every 8 minutes
        ├── Job 3: NewsAPI Collector            → every 15 minutes
        └── Job 4: Classification + Geo + Alert Pipeline → every 10 minutes
```

All jobs use lazy imports to avoid circular dependency issues.
Each job has independent try/except with error logging — one failure doesn't stop others.

---

## 🔄 Full Pipeline Flow

```
COLLECTION (every 3–15 min per source)
  HTTP GET → parse XML/JSON → keyword_filter (+ negative kw exclusion)
  → normalize → dedup_hash check → insert raw_events

PROCESSING (every 10 min)
  Fetch raw_events where is_processed = False (oldest-first, limit 50)
    │
    For each event:
    ├── Rule Classifier       → conf >= 0.75? → use it  (< 1ms)
    ├── ML Classifier         → conf >= 0.55? → use it  (~50ms cached)
    └── Gemini 2.5 Flash      → max 10 calls/cycle      (~1-2s)
    │
    ├── Drop if conf < 0.3 or type == "unknown"
    ├── Severity Detector     → HIGH / MEDIUM / LOW
    ├── spaCy NER             → extract GPE/LOC entities
    ├── Alias Normalizer      → Bombay → Mumbai (title-case)
    ├── Nominatim Resolver    → geo_cache hit → return | miss → API + cache
    ├── Skip if no valid location resolved (no fake coords)
    ├── Spatial Dedup ($near) → within 50km + 12hr? → increment source_count, skip insert
    └── Insert processed_events (GeoJSON [lon, lat])
    │
    Mark raw_event is_processed = True

POST-PROCESSING
  DBSCAN clustering (eps=100km, min_samples=2, ball_tree haversine)
    → assign cluster_id "CL-{first8chars}" to grouped events
  Alert Engine
    → scan last 12hr events, skip already-alerted event_ids
    → calculate risk_score (0-100)
    → if risk_score >= 45: get Gemini safety advice (1hr cache) → insert alert
```

---

## 🌐 Data Sources

| Source | Type | Interval | Free? | Key Needed? |
|---|---|---|---|---|
| NDMA CAP | XML/CAP | 3 min | ✅ | ❌ |
| Times of India RSS | XML/RSS | 8 min | ✅ | ❌ |
| The Hindu RSS | XML/RSS | 8 min | ✅ | ❌ |
| Indian Express RSS | XML/RSS | 8 min | ✅ | ❌ |
| NDTV RSS | XML/RSS | 8 min | ✅ | ❌ |
| Hindustan Times RSS | XML/RSS | 8 min | ✅ | ❌ |
| NewsAPI | JSON | 15 min | ✅ (100/day) | ✅ `NEWS_API_KEY` |

**Source Reliability Weights:**
| Source | Weight |
|---|---|
| NDMA | 0.95 |
| NewsAPI | 0.80 |
| RSS (all) | 0.70 |

---

## 🤖 Classification Pipeline

```
Input: title + description
  │
  ├─ STEP 1: Rule Classifier (< 1ms)
  │     Regex patterns for: flood, earthquake, cyclone, landslide,
  │                         heatwave, fire, tsunami, storm
  │     Returns (disaster_type, 0.75) on match
  │     If conf >= 0.75 → DONE ✓
  │
  ├─ STEP 2: ML Classifier (~500ms first run, ~50ms cached)
  │     Model: valhalla/distilbart-mnli-12-3 (singleton)
  │     Zero-shot against 8 candidate labels
  │     If score >= 0.55 → DONE ✓
  │
  └─ STEP 3: Gemini 2.5 Flash Fallback (~1-2s)
        Only when confidence < 0.55
        Hard cap: 10 calls per pipeline cycle
        JSON output: { disaster_type, confidence }
        "none" type → returns ("unknown", 0.0)
```

**Severity Detection Rules:**
```
HIGH   → killed, dead, deaths, destroyed, evacuat, rescue, collapse,
         casualties, fatalities, massive, severe damage, catastrophe,
         emergency, tragedy, devastation
MEDIUM → warning, alert, watch, expected, possible, risk, forecast,
         approaching, moderate, threat
LOW    → (default fallback)
```

---

## 📍 Geo Pipeline

```
Raw text: "Flood in Guwahati, Assam"
    │
    spaCy NER (en_core_web_sm) → GPE/LOC entities → ["Guwahati", "Assam"]
    │
    Alias check → normalize_location("Guwahati") → "Guwahati" (no alias)
    │
    geo_cache lookup → key: "guwahati, india"
      → Hit?  Return cached (lat, lon, display_name)
      → Miss? Nominatim geocode → sleep(1.1s) → cache → return
    │
    Store as GeoJSON: { "type": "Point", "coordinates": [91.7362, 26.1445] }
    │
    MongoDB $near check (50km / 12hr same disaster_type)
      → Duplicate? increment source_count, skip insert
      → New?      insert processed_events
```

**NER Known Limitations (spaCy en_core_web_sm):**
- Success rate: ~60-70% for Indian locations
- Works well: Mumbai, Delhi, Bangalore, Kolkata, Uttarakhand, Dehradun, Jaipur
- Struggles with: Chennai, Assam, Maharashtra, Tamil Nadu, Puducherry
- Events with no extractable location are skipped (no fake coordinates inserted)

---

## 🚨 Alert Engine

**Trigger:** `risk_score >= 45`

**Risk Score Formula (0-100):**
```
base        = HIGH→50, MEDIUM→25, LOW→10
corroboration = min(30, (source_count - 1) * 2)
raw_score   = base + corroboration
adjusted    = raw_score * max(0.2, confidence)
bonus       = ×1.2 if HIGH + source_count>=5 + confidence>=0.8
final       = clamp(int(adjusted), 0, 100)
```

**Safety Advice:** Gemini 2.5 Flash, 2 concise sentences, cached 1hr per (disaster_type, severity).
Static fallback templates for: flood, earthquake, cyclone, fire, heatwave.

**Deduplication:** One alert per event_id — checked via indexed `event_id` lookup.

---

## 🌍 FastAPI Endpoints

| Method | Endpoint | Description | Status |
|---|---|---|---|
| GET | `/` | Health check | ✅ |
| GET | `/api/docs` | Swagger UI (auto-generated) | ✅ |
| GET | `/api/redoc` | ReDoc UI (auto-generated) | ✅ |
| GET | `/api/events` | List events (filter: type, severity, state, hours, limit) | ✅ |
| GET | `/api/events/{id}` | Single event detail | ✅ (bug fixed 2026-04-10) |
| GET | `/api/alerts` | Recent alerts (with limit) | ✅ |
| GET | `/api/stats` | Summary counts by type + severity | ✅ |
| GET | `/api/heatmap` | Coordinates + severity weights for map | ✅ |
| GET | `/api/risk/{location}` | Risk score for a location (24hr window) | ✅ |
| POST | `/api/pipeline/run` | Manually trigger pipeline (BackgroundTasks) | ✅ |

**Verified live:** All 10 routes registered and returning correct responses.
**CORS:** Configured for all origins (tighten for production).

**Bug Fixed (2026-04-10):**
`GET /api/events/{id}` was returning 500 due to missing `raw_event_id` ObjectId → string
conversion. Fixed in `src/api/routes/events.py`.

---

## 🖥️ Streamlit Dashboard

| Page | File | Status |
|---|---|---|
| Home (stats + navigation) | `app.py` | ✅ Functional |
| Live event feed + cards | `dashboard/pages/1_Home.py` | ❌ Not created |
| Folium map + clusters | `dashboard/pages/2_Map.py` | ❌ Not created |
| Plotly charts + analytics | `dashboard/pages/3_Analytics.py` | ❌ Not created |
| Alert history + risk scores | `dashboard/pages/4_Alerts.py` | ❌ Not created |
| Sidebar component | `dashboard/components/sidebar.py` | ❌ Missing (app.py imports it → crash) |
| Event card component | `dashboard/components/event_card.py` | ❌ Not created |
| Map builder utility | `dashboard/components/map_builder.py` | ❌ Not created |

> ⚠️ `app.py` imports `from dashboard.components.sidebar import render_sidebar` — this will
> crash on `streamlit run app.py` until `sidebar.py` is created.

---

## ☁️ AWS Deployment Strategy

```
MongoDB Atlas (free 512MB) ← cloud database
        │
EC2 t2.micro (free tier)
  ├── FastAPI (uvicorn, port 8000)
  ├── APScheduler (background jobs)
  └── Streamlit (port 8501)
        │
systemd service → keeps process alive 24/7
```

**systemd service** (`/etc/systemd/system/geopulse.service`):
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

Switch to Atlas: change `MONGO_URI` in `.env` — zero code change.

---

## 🔐 Environment Variables (`.env`)

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB=disaster_db
GEMINI_API_KEY=your_gemini_key_here
NEWS_API_KEY=your_newsapi_key_here
LLM_MAX_CALLS_PER_CYCLE=10
ML_CONFIDENCE_THRESHOLD=0.55
RULE_CONFIDENCE_THRESHOLD=0.75
DEDUP_RADIUS_KM=50
DEDUP_TIME_WINDOW_HOURS=12
API_PORT=8000
```

---

## 📦 Dependencies

Managed via `uv` + `pyproject.toml`. Install with `uv sync`.

Key packages: `fastapi`, `uvicorn[standard]`, `streamlit`, `streamlit-folium`, `folium`,
`pymongo`, `apscheduler`, `feedparser`, `httpx`, `lxml`, `newsapi-python`, `spacy`,
`transformers`, `torch`, `google-genai`, `geopy`, `scikit-learn`, `numpy`,
`python-dotenv`, `pytz`, `plotly`, `pandas`

```bash
uv sync
python -m spacy download en_core_web_sm
```

---

## ✅ Phase Execution Checklist

---

### ✅ Phase 0 — Setup & Scaffolding `COMPLETE`

- [x] `pyproject.toml` — 40+ dependencies, uv-compatible
- [x] `requirements.txt` — human-readable with inline comments
- [x] `.env.example` — 10 variables documented
- [x] `.gitignore` — covers `.env`, `__pycache__`, `.venv`, HuggingFace cache
- [x] All `__init__.py` files created for every package
- [x] `src/db/database.py` — singleton MongoClient, ping on startup, all indexes
- [x] `src/db/crud.py` — complete CRUD layer, only file that touches MongoDB
- [x] `src/scheduler/jobs.py` — APScheduler, Asia/Kolkata, lazy imports, per-job error handling
- [x] `src/api/app.py` — FastAPI factory, CORS, docs at `/api/docs`
- [x] All 4 route modules — events, alerts, stats, pipeline
- [x] `main.py` — ordered startup: DB init → scheduler → uvicorn
- [x] `app.py` — Streamlit home page with live stats
- [x] All packages installed via `uv sync`
- [x] `en_core_web_sm` v3.8.0 installed

---

### ✅ Phase 1 — Data Collection `COMPLETE`

- [x] `src/processors/keyword_filter.py` — disaster keywords + negative keyword exclusion
- [x] `src/processors/normalizer.py` — NDMA / RSS / NewsAPI → common schema
- [x] `src/processors/deduplicator.py` — SHA256 hash (source + title[:60] + hour bucket)
- [x] `src/collectors/ndma_collector.py` — CAP XML + Atom fallback, ETag caching
- [x] `src/collectors/rss_collector.py` — 5 feeds (TOI, Hindu, Express, NDTV, HT), 1s inter-feed delay
- [x] `src/collectors/newsapi_collector.py` — 4 search queries, 96/100 daily limit safe

---

### ✅ Phase 2 — Classification `COMPLETE`

- [x] `src/classifiers/rule_classifier.py` — compiled regex, 8 disaster types
- [x] `src/classifiers/ml_classifier.py` — distilbart-mnli-12-3 singleton, 8 candidate labels
- [x] `src/classifiers/llm_fallback.py` — Gemini 2.5 Flash, JSON output, "none" → unknown
- [x] `src/classifiers/severity_detector.py` — HIGH/MEDIUM/LOW compiled regex
- [x] `src/classifiers/pipeline.py` — full 3-tier chain + geo + dedup + clustering + alerts

---

### ✅ Phase 3 — Geo + Clustering `COMPLETE`

- [x] `src/geo/ner_extractor.py` — spaCy GPE/LOC, singleton, max 10000 chars, deduped output
- [x] `src/geo/loc_normalizer.py` — alias dict, title-case values (Bombay→Mumbai)
- [x] `src/geo/geo_resolver.py` — Nominatim, 1.1s rate limit, MongoDB geo_cache
- [x] `src/geo/spatial_dedup.py` — MongoDB $near (50km / 12hr), increments source_count
- [x] `src/geo/clusterer.py` — DBSCAN (eps=100km, ball_tree, haversine), cluster_id "CL-{id[:8]}"

---

### ✅ Phase 4 — Alerts + Intelligence `COMPLETE`

- [x] `src/alerts/risk_scorer.py` — composite 0-100 score (severity + corroboration + confidence)
- [x] `src/alerts/safety_advisor.py` — Gemini 2.5 Flash, 1hr TTL cache, static fallback templates
- [x] `src/alerts/alert_engine.py` — threshold >= 45, dedup by event_id, timezone-aware timestamps

---

### ✅ Full Codebase Verification — `2026-04-10` — PASSED 21/21

**verify_all.py:** 21/21 PASS
**verify_api.py:** 8/8 expected routes registered ✅

**All bugs fixed as of 2026-04-10:**

| File | Bug | Fix |
|---|---|---|
| `keyword_filter.py` | `_PHRASE_PATTERN` undefined | Restored definition |
| `rule_classifier.py` | `\bloods?\b` matched "blood" | Fixed to `\bfloods?\b` |
| `pipeline.py` | `_llm_calls_this_cycle` undeclared | Added module-level `= 0` |
| `loc_normalizer.py` | Dict values lowercase | Fixed to title-case |
| `llm_fallback.py` | Deprecated `google-generativeai` | Migrated to `google-genai` SDK |
| `ner_extractor.py` | "FAC" entity type included | Removed (caused building name extraction) |
| `pipeline.py` | Forced `.title()` on locations | Removed to preserve casing |
| `pipeline.py` | Fake fallback coordinates | Now skips events with no valid location |
| `pipeline.py` | Missing fields in processed_events | Added `source_count`, `source_reliability`, `is_active`, `created_at` |
| `alert_engine.py` | Missing `created_at` | Added timezone-aware datetime |
| `alert_engine.py` | No handling for missing location | Added fallback to "Unknown Location" |
| `api/routes/events.py` | `GET /api/events/{id}` → 500 | Added `raw_event_id` ObjectId→str conversion |

---

### 🟡 Phase 5 — Streamlit Dashboard `User Choice Streamlit or Other frontend`

**Complete:**
- [x] `app.py` — Home page: live metrics (events, severity, alerts, pending raw), event type breakdown, navigation guide

**Missing (dashboard will crash until sidebar.py is created):**
- [ ] `dashboard/components/sidebar.py` — `render_sidebar()` function (imported by app.py)
- [ ] `dashboard/components/event_card.py` — reusable event card
- [ ] `dashboard/components/map_builder.py` — Folium map builder
- [ ] `dashboard/pages/1_Home.py` — live event feed with auto-refresh
- [ ] `dashboard/pages/2_Map.py` — Folium map + MarkerCluster + heatmap overlay
- [ ] `dashboard/pages/3_Analytics.py` — Plotly charts (type/severity/timeline/state)
- [ ] `dashboard/pages/4_Alerts.py` — alert history + risk score cards + safety tips

---

### 🔲 Phase 6 — Integration & Polish `NOT STARTED`

- [ ] Fix dashboard crash: create `dashboard/components/sidebar.py`
- [ ] Complete all 4 dashboard pages + 3 components
- [ ] End-to-end test: collection → classification → map marker visible
- [ ] Mock data fallback (for when feeds are offline)
- [ ] `README.md` — setup instructions + architecture diagram
- [ ] Performance optimization and error handling review
- [ ] Deployment guide (EC2 + Atlas)

---

## 📊 Current Live Database State (as of 2026-04-10)

| Collection | Count | Notes |
|---|---|---|
| `raw_events` | 23 | 0 pending (all processed) |
| `processed_events` | 11 | flood:2, storm:3, fire:3, landslide:2, earthquake:1 |
| `alerts` | 0 | No events have breached risk threshold yet |
| `geo_cache` | 10 | Nominatim results cached |

**Severity breakdown:** HIGH:6, MEDIUM:1, LOW:4
**Heatmap points:** 7 events with valid geo coordinates

---

## 🔥 Known Risks & Mitigations

| Risk | Mitigation |
|---|---|
| NDMA feed down / URL changes | try/except, skip cycle, Atom fallback parser |
| Nominatim rate limit (1 req/s) | geo_cache collection, sleep(1.1s) enforced |
| HuggingFace slow first load | Singleton loaded at first pipeline run |
| Gemini API cost overrun | Hard cap 10 calls/cycle, 1hr cache for safety tips |
| NewsAPI 100/day limit | 15-min interval = 96 req/day (within limit) |
| MongoDB write concurrency | pymongo handles natively |
| GeoJSON lon/lat order confusion | Always [lon, lat], documented in crud.py |
| spaCy low Indian NER accuracy | ~60-70% success rate; events without location skipped |
| Dashboard crash on startup | sidebar.py missing — must be created before `streamlit run app.py` |

---

## 🎯 Next Priority

1. **Immediate — Fix dashboard crash:**
   Create `dashboard/components/sidebar.py` with `render_sidebar()` so `streamlit run app.py` works.

2. **Short-term — Complete Phase 5:**
   - `dashboard/pages/1_Home.py` — event cards with `st.rerun()` auto-refresh
   - `dashboard/pages/2_Map.py` — Folium + MarkerCluster + streamlit-folium
   - `dashboard/pages/3_Analytics.py` — Plotly bar/pie/timeline charts
   - `dashboard/pages/4_Alerts.py` — alert list + risk score calculator
   - `dashboard/components/event_card.py` and `map_builder.py`

3. **Long-term — Phase 6:**
   - README with architecture diagram
   - AWS EC2 + MongoDB Atlas deployment guide
   - Mock data fallback for offline feeds

---

*Last updated: 2026-04-10 | Phases 0–4 complete ✅ | API verified 10/10 ✅ | verify_all 21/21 ✅ | Phase 5 partial 🟡 | Phase 6 not started 🔲*
