"""Simple Streamlit UI for browsing local gym events."""
from __future__ import annotations

import requests
import streamlit as st

API_BASE = "http://localhost:8000"

st.set_page_config(layout="wide", page_title="Gym MVP Local")
st.title("Gym behavior tracking MVP (local)")

col1, col2 = st.columns(2)
with col1:
    event_type = st.selectbox("Event type", ["", "MACHINE_OCCUPIED_START", "MACHINE_OCCUPIED_END", "CLEANING_WINDOW_OPEN", "CLEANING_ATTEMPT"])
with col2:
    zone_id = st.text_input("Zone ID", value="")

params = {"limit": 200}
if event_type:
    params["event_type"] = event_type
if zone_id:
    params["zone_id"] = zone_id

try:
    events = requests.get(f"{API_BASE}/events", params=params, timeout=3).json()
except Exception as exc:
    st.error(f"Backend unavailable: {exc}")
    st.stop()

if not events:
    st.info("No events yet. Run edge_service to generate data.")
    st.stop()


show_cols = ["event_id", "ts_utc", "event_type", "camera_id", "zone_id", "mm_status"]
rows = [{k: e.get(k) for k in show_cols} for e in events]
st.dataframe(rows, use_container_width=True)

selected = st.selectbox("Select event", [e["event_id"] for e in events])
if selected:
    detail = requests.get(f"{API_BASE}/events/{selected}", timeout=3).json()
    st.subheader("Event detail")
    st.json(detail)
    st.markdown(f"**MM Description:** {detail.get('mm_description')}")
    st.video(f"{API_BASE}/media/{selected}")
