"""
app.py
──────
Streamlit dashboard entry point.

Run with:  streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="GeoPulse Intelligence",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🚨 GeoPulse Intelligence")
st.caption("Real-time Disaster Monitoring System — India")
st.info(
    "⚙️ **Phase 0 complete.** Database layer and API skeleton are ready.\n\n"
    "Dashboard pages will appear here as each phase is implemented.",
    icon="ℹ️",
)

# Sidebar
with st.sidebar:
    st.header("GeoPulse")
    st.markdown("**Status:** 🟢 Running")
    st.markdown("Navigate using the **Pages** menu above.")
