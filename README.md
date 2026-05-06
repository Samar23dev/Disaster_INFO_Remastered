# 🚨 GeoPulse Intelligence — Disaster Information System

> Real-time disaster event monitoring, NLP classification, and geospatial visualization.

GeoPulse Intelligence is a robust system that aggregates disaster-related news from various sources (NDMA, RSS feeds, NewsAPI), classifies them using a multi-tiered AI pipeline, extracts geographic locations, and visualizes them on an interactive dashboard.

---

## 🏗️ Architecture

```text
Data Sources (NDMA, RSS, NewsAPI)
      │
      ▼
APScheduler Background Jobs (Data Collection)
      │
      ▼
Classification Pipeline:
  1. Rule-Based Classifier (Fast keyword match)
  2. ML Classifier (distilbart-mnli-12-3)
  3. LLM Fallback (Gemini 2.5 Flash)
      │
      ▼
Geo-Resolution (spaCy NER → Nominatim Geocoding)
      │
      ▼
MongoDB Spatial Deduplication ($near) & Clustering
      │
      ▼
FastAPI REST Endpoints
      │
      ▼
React / Streamlit Dashboard
```

---

## 🧱 Tech Stack

- **Backend:** Python 3.11+, FastAPI, Uvicorn
- **Data Pipeline:** APScheduler, httpx, lxml, feedparser
- **NLP & AI:** spaCy, HuggingFace (`distilbart-mnli-12-3`), Gemini 2.5 Flash
- **Database:** MongoDB (with native geo queries)
- **Frontend:** React + Vite + TailwindCSS (Primary), Streamlit (Alternative)
- **Dependency Management:** `uv`

---

## 📁 Project Structure

```text
DisasterManagement/
├── main.py                 # FastAPI & APScheduler entry point
├── pyproject.toml / uv.lock # Dependencies managed via uv
├── .env.example            # Environment variables template
├── src/                    # Backend logic (db, collectors, processors, api)
├── reactfrontend/          # Modern React + Vite Web Dashboard
├── dashboard/              # Streamlit dashboard alternative
└── IMPLEMENTATION_PLAN.md  # Detailed system architecture
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.11+
- Node.js (for the React frontend)
- `uv` (Python package manager)
- MongoDB (Local instance or MongoDB Atlas)

### 1. Environment Variables
Clone the repository and set up your `.env` file:
```bash
cp .env.example .env
```
Edit `.env` to include your API keys:
```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB=disaster_db
GEMINI_API_KEY=your_gemini_api_key_here
NEWS_API_KEY=your_newsapi_key_here
```

### 2. Run the Backend (FastAPI + Pipeline)
```bash
# Install Python dependencies using uv
uv sync

# Download the spaCy NER model
uv run python -m spacy download en_core_web_sm

# Start the FastAPI server and background jobs
uv run python main.py
```
*The backend API will run on `http://localhost:8000`. You can view the Swagger UI at `http://localhost:8000/api/docs`.*

### 3. Run the Frontend (React)
Open a new terminal window:
```bash
cd reactfrontend
npm install
npm run dev
```
*The React dashboard will run at `http://localhost:5173`.*

---

## 🌐 API Endpoints

- `GET /api/events` - List filtered events
- `GET /api/events/{id}` - Single event detail
- `GET /api/alerts` - Recent disaster alerts
- `GET /api/stats` - Summary counts
- `GET /api/heatmap` - Coordinates for map overlay
- `POST /api/pipeline/run` - Manually trigger data processing

---

## ✨ React Frontend Features

The modern React dashboard provides a premium, responsive interface for situational awareness:

- **Interactive Geospatial Map:** View clustered disaster events globally using Leaflet, complete with severity-based color coding.
- **Live Event Feed:** A real-time updating timeline of all collected intelligence.
- **Alert Management:** Track and view high-risk disaster alerts along with AI-generated safety protocols.
- **Data Analytics:** Visual summaries of disaster occurrences categorized by type and severity level.
