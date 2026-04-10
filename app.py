"""
app.py
──────
GeoPulse Intelligence — Streamlit dashboard entry point.

Run with:
    streamlit run app.py
    (or: uv run streamlit run app.py)

This is the "Home" landing screen. Use the sidebar pages to navigate:
    🏠 Home       — Live event feed
    🗺️ Map        — Interactive Folium map
    📊 Analytics  — Charts + state breakdown
    🚨 Alerts     — Alert history + risk scores
"""

import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GeoPulse Intelligence",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)

from dashboard.components.sidebar import render_sidebar

# ── Sidebar (with live status + filters) ─────────────────────────────────────
filters = render_sidebar()

# ── Hero header ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="text-align:center; padding: 32px 0 16px 0;">
        <h1 style="font-size:3rem; margin-bottom:4px;">🚨 GeoPulse Intelligence</h1>
        <p style="font-size:1.15rem; color:#888; margin:0;">
            Real-time Disaster Monitoring System &nbsp;·&nbsp; India
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# ── Live stats row ────────────────────────────────────────────────────────────
try:
    from src.db.crud import get_stats, get_recent_alerts, count_raw_events

    stats = get_stats()
    alerts = get_recent_alerts(limit=50)
    unread_alerts = len([a for a in alerts if not a.get("is_read", False)])
    pending_raw = count_raw_events(processed=False)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("📊 Active Events", stats.get("total_events", 0))
    with c2:
        by_sev = stats.get("by_severity", {})
        st.metric("🔴 HIGH Severity", by_sev.get("HIGH", 0))
    with c3:
        st.metric("🟡 MEDIUM Severity", by_sev.get("MEDIUM", 0))
    with c4:
        st.metric("🚨 Unread Alerts", unread_alerts)
    with c5:
        st.metric("⏳ Pending Raw", pending_raw)

    st.divider()

    # ── Most common disaster types ────────────────────────────────────────────
    by_type = stats.get("by_type", {})
    if by_type:
        st.subheader("🌍 Event Breakdown")
        sorted_types = sorted(by_type.items(), key=lambda x: x[1], reverse=True)

        cols = st.columns(min(len(sorted_types), 5))
        type_emojis = {
            "flood": "🌊", "earthquake": "🌋", "cyclone": "🌀",
            "landslide": "⛰️", "heatwave": "🔥", "fire": "🔥",
            "tsunami": "🌊", "storm": "⛈️", "cloudburst": "🌧️",
        }
        for i, (dtype, count) in enumerate(sorted_types[:5]):
            with cols[i]:
                emoji = type_emojis.get(dtype.lower(), "❓")
                st.metric(f"{emoji} {dtype.capitalize()}", count)

except Exception as exc:
    st.warning(
        f"⚠️ Could not load stats from MongoDB: {exc}\n\n"
        "Make sure MongoDB is running and `.env` is configured.",
        icon="⚠️",
    )

st.divider()

# ── Navigation guide ──────────────────────────────────────────────────────────
st.subheader("🧭 Navigate the Dashboard")

nav1, nav2, nav3, nav4 = st.columns(4)

with nav1:
    st.markdown(
        """
        <div style="border:1px solid #333; border-radius:12px; padding:20px; text-align:center;">
            <h3>🏠 Live Feed</h3>
            <p style="color:#888; font-size:0.9rem;">
                Browse all recent disaster events as color-coded cards.
                Auto-refreshes every 60 s.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with nav2:
    st.markdown(
        """
        <div style="border:1px solid #333; border-radius:12px; padding:20px; text-align:center;">
            <h3>🗺️ Map</h3>
            <p style="color:#888; font-size:0.9rem;">
                Interactive Folium map with clustered markers and
                optional heatmap overlay.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with nav3:
    st.markdown(
        """
        <div style="border:1px solid #333; border-radius:12px; padding:20px; text-align:center;">
            <h3>📊 Analytics</h3>
            <p style="color:#888; font-size:0.9rem;">
                Plotly charts — disaster type breakdown, severity distribution,
                timeline, and top states.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with nav4:
    st.markdown(
        """
        <div style="border:1px solid #333; border-radius:12px; padding:20px; text-align:center;">
            <h3>🚨 Alerts</h3>
            <p style="color:#888; font-size:0.9rem;">
                Alert history with Gemini-generated safety advice
                and a risk score calculator.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()
st.caption(
    "GeoPulse Intelligence · Phases 0–5 Complete · "
    "Stack: Python · FastAPI · MongoDB · spaCy · HuggingFace · Gemini · Streamlit"
)
