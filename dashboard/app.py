"""
Interactive Streamlit Security Command Dashboard for FlytBase Drone Security Analyst Agent.
Enables real-time patrol simulation, live telemetry HUD, real-time alert dispatch,
semantic cross-domain frame search, and conversational LangChain Q&A.
"""

import os
import sys
import time
from PIL import Image
import streamlit as st

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.pipeline import DroneSecurityPipeline
from src.telemetry.models import AlertSeverity

# Page configuration
st.set_page_config(
    page_title="FlytBase - Autonomous Drone Security Analyst",
    page_icon="🛸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Tactical Styling
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
    .main-header {
        font-size: 26px;
        font-weight: 700;
        color: #00ff88;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 14px;
        color: #a0aec0;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #1a202c;
        border: 1px solid #2d3748;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    .alert-critical {
        background-color: rgba(220, 38, 38, 0.15);
        border-left: 4px solid #ef4444;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .alert-warning {
        background-color: rgba(234, 179, 8, 0.15);
        border-left: 4px solid #eab308;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .stTextInput > div > div > input {
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State & Pipeline
@st.cache_resource
def get_pipeline():
    pipeline = DroneSecurityPipeline()
    pipeline.run_all_patrols()
    return pipeline

pipeline = get_pipeline()

# Header
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown('<div class="main-header">🛸 FlytBase Drone Security Analyst Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Docked Autonomous Drone (DiaB) Real-Time Perimeter Surveillance & VLM Analytics</div>', unsafe_allow_html=True)
with col_status:
    st.success("🟢 DiaB DOCK ONLINE | VLM READY")

# Sidebar Controls
st.sidebar.image("https://img.icons8.com/fluency/96/drone.png", width=64)
st.sidebar.title("Patrol Mission Control")

available_missions = pipeline.simulator.get_all_missions()
selected_mission = st.sidebar.selectbox(
    "Select Autonomous Mission",
    ["ALL MISSIONS"] + available_missions,
    index=0
)

# Filter frames & alerts
all_frames = pipeline.processed_frames
if selected_mission != "ALL MISSIONS":
    filtered_frames = [f for f in all_frames if f.mission_id == selected_mission]
else:
    filtered_frames = all_frames

filtered_alerts = [a for a in pipeline.triggered_alerts if selected_mission == "ALL MISSIONS" or a.mission_id == selected_mission]

st.sidebar.markdown("---")
st.sidebar.subheader("System Telemetry Health")
st.sidebar.metric("Battery State", "96%", delta="Solar Charging")
st.sidebar.metric("Dock Station", "Bay Alpha (North)", delta="LOCKED")
st.sidebar.metric("Curfew Status", "ACTIVE (22:00 - 06:00)", delta="ENFORCING")

# Top High-Level Metrics
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Total Frames Analyzed", len(filtered_frames))
with m2:
    st.metric("Security Alerts", len(filtered_alerts), delta=f"{sum(1 for a in filtered_alerts if a.severity == AlertSeverity.CRITICAL)} Critical", delta_color="inverse")
with m3:
    tracked_count = len(pipeline.context.get_all_entities())
    st.metric("Tracked Entities", tracked_count)
with m4:
    unique_zones = len(set(f.telemetry.zone_name for f in filtered_frames))
    st.metric("Zones Monitored", unique_zones)

# Main Navigation Tabs
tab_live, tab_alerts, tab_search, tab_agent, tab_summary = st.tabs([
    "📹 Live Patrol HUD & Frames",
    "🚨 Real-Time Security Alerts",
    "🔍 Cross-Domain Semantic Search",
    "🤖 LangChain Security Analyst Chat",
    "📋 Video Summarizer & Debrief"
])

# =========================================================================
# TAB 1: LIVE PATROL HUD & FRAMES
# =========================================================================
with tab_live:
    st.subheader("Autonomous Drone Video Feed & Frame-by-Frame VLM Inference")
    
    col_player, col_meta = st.columns([3, 2])
    
    if filtered_frames:
        frame_idx = st.slider("Scrub Video Timeline (Frame Sequence)", 0, len(filtered_frames) - 1, 0)
        curr_frame = filtered_frames[frame_idx]
        
        with col_player:
            # Display annotated tactical frame
            ann_path = os.path.join("data/annotated_frames", f"annotated_{curr_frame.frame_id}.png")
            disp_path = ann_path if os.path.exists(ann_path) else curr_frame.image_path
            
            st.image(disp_path, use_container_width=True, caption=f"Tactical Feed: {curr_frame.frame_id} [{curr_frame.timestamp}]")
            
            if curr_frame.is_alert:
                st.error(f"⚠️ Incident Flagged on this Frame: {curr_frame.caption}")
            else:
                st.info(f"ℹ️ Status: Sector Clear | {curr_frame.caption}")

        with col_meta:
            st.markdown("#### 📡 Real-Time Telemetry HUD")
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                st.metric("Altitude (AGL)", f"{curr_frame.telemetry.altitude_m:.1f} m")
                st.metric("Flight Speed", f"{curr_frame.telemetry.speed_mps:.1f} m/s")
            with t_col2:
                st.metric("Zone Location", curr_frame.telemetry.zone_name)
                st.metric("Battery Remaining", f"{curr_frame.telemetry.battery_pct:.0f}%")

            st.markdown("#### 🧠 VLM & Context Derivation")
            st.write(f"**Caption:** {curr_frame.caption}")
            st.write(f"**Activity Inference:** {curr_frame.activity_summary}")
            
            if curr_frame.detected_objects:
                st.write("**Detected Entities:**")
                for obj in curr_frame.detected_objects:
                    st.write(f"- `{obj.description}` ({obj.label}) — Conf: {obj.confidence:.2f}")
            else:
                st.write("*No objects detected in current field of view.*")

# =========================================================================
# TAB 2: REAL-TIME SECURITY ALERTS
# =========================================================================
with tab_alerts:
    st.subheader("Incident Timeline & Active Security Dispatches")
    
    if not filtered_alerts:
        st.success("No active security violations in the selected mission filter.")
    else:
        for alert in filtered_alerts:
            css_class = "alert-critical" if alert.severity == AlertSeverity.CRITICAL else "alert-warning"
            icon = "🚨" if alert.severity == AlertSeverity.CRITICAL else "⚠️"
            
            st.markdown(f"""
            <div class="{css_class}">
                <div style="font-weight: 700; font-size: 16px;">
                    {icon} [{alert.severity.value}] {alert.description}
                </div>
                <div style="font-size: 13px; color: #cbd5e1; margin-top: 4px;">
                    <strong>Timestamp:</strong> {alert.timestamp} &nbsp;|&nbsp; 
                    <strong>Zone:</strong> {alert.zone_name} &nbsp;|&nbsp; 
                    <strong>Rule:</strong> <code>{alert.rule_name}</code>
                </div>
                <div style="font-size: 13px; margin-top: 6px;">
                    <strong>Context / Reasoning:</strong> {alert.context_reason}
                </div>
                <div style="font-size: 13px; color: #38bdf8; margin-top: 4px;">
                    <strong>Suggested Action:</strong> {alert.suggested_action}
                </div>
            </div>
            """, unsafe_allow_html=True)

# =========================================================================
# TAB 3: CROSS-DOMAIN SEMANTIC SEARCH (ChromaDB + SQLite)
# =========================================================================
with tab_search:
    st.subheader("Cross-Domain Frame Search Engine")
    st.caption("Search across all indexed drone surveillance frames using natural language or entity names (e.g., 'show all truck events', 'person loitering at gate').")

    search_query = st.text_input(
        "Enter Natural Language Search Query:",
        value="show all truck events",
        help="Query video frames using natural language semantic similarity"
    )

    if search_query:
        results = pipeline.vector_store.search(search_query, top_k=4)
        
        st.markdown(f"**Found {len(results)} matching frame(s) for query:** `\"{search_query}\"`")
        
        cols = st.columns(len(results)) if results else []
        for i, res in enumerate(results):
            meta = res.get("metadata", {})
            score = res.get("score", 1.0)
            img_p = meta.get("image_path", "")
            
            with cols[i]:
                if os.path.exists(img_p):
                    st.image(img_p, use_container_width=True)
                st.markdown(f"**{meta.get('frame_id')}** (Match: {score*100:.1f}%)")
                st.caption(f"🕒 {meta.get('timestamp')} | 📍 {meta.get('zone_name')}")
                st.write(f"*{res.get('document', '')[:120]}...*")

# =========================================================================
# TAB 4: LANGCHAIN CONVERSATIONAL AGENT CHAT
# =========================================================================
with tab_agent:
    st.subheader("Conversational Security Analyst Agent")
    st.caption("Ask questions about the property, vehicles seen, dwell times, and patrol findings.")

    # Suggested query buttons
    s1, s2, s3, s4 = st.columns(4)
    sample_q = None
    if s1.button("What objects were in the video?"):
        sample_q = "What objects were in the video?"
    if s2.button("Show all truck events"):
        sample_q = "Show all truck events"
    if s3.button("Did the blue Ford F150 enter twice?"):
        sample_q = "Did the blue Ford F150 enter twice today?"
    if s4.button("What alerts triggered at midnight?"):
        sample_q = "What alerts triggered at midnight?"

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Hello Commander. I am your autonomous Drone Security Analyst Agent. How can I assist you with today's patrol data?"}
        ]

    user_input = st.chat_input("Ask about drone surveillance, alerts, or vehicle history...")
    actual_query = sample_q or user_input

    if actual_query:
        st.session_state.chat_history.append({"role": "user", "content": actual_query})
        response = pipeline.agent.answer_query(actual_query)
        st.session_state.chat_history.append({"role": "assistant", "content": response})

    # Render Chat History
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# =========================================================================
# TAB 5: VIDEO PATROL SUMMARIZER & DEBRIEF (Bonus Feature)
# =========================================================================
with tab_summary:
    st.subheader("Automated Patrol Flight Debrief & Video Summarization")
    
    # Calculate mission summary
    active_m_id = selected_mission if selected_mission != "ALL MISSIONS" else "PATROL_ALL_SECTORS"
    summary = pipeline.rules.context.get_all_entities()
    
    # Generate executive summary
    from src.agent.summarizer import PatrolVideoSummarizer
    patrol_sum = PatrolVideoSummarizer.generate_summary(active_m_id, filtered_frames, filtered_alerts)
    
    st.markdown("### 📌 1-Sentence Executive Summary")
    st.info(patrol_sum.one_sentence_summary)

    st.markdown("### 📝 Full Autonomous Mission Debrief")
    st.code(patrol_sum.executive_summary, language="markdown")

    st.markdown("### ⏱️ Chronological Key Events")
    for event in patrol_sum.key_events:
        st.write(f"- {event}")

# Footer
st.markdown("---")
st.caption("FlytBase Drone Security Analyst Agent Prototype | Built for Autonomous DiaB Operations | Python, LangChain, Transformers, ChromaDB, SQLite, Streamlit")
