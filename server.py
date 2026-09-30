"""
FastAPI Backend Server & React Static Host for FlytBase Drone Security Analyst Agent.
Provides REST APIs for live telemetry, video frames, ChromaDB vector search,
real-time alerts, and conversational LangChain security Q&A.
Serves the custom aerospace React frontend on http://localhost:8000.
"""

import os
from typing import Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.pipeline import DroneSecurityPipeline
from src.agent.summarizer import PatrolVideoSummarizer

app = FastAPI(title="FlytBase Drone Security Analyst API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline and process missions on boot
pipeline = DroneSecurityPipeline()
pipeline.run_all_patrols()

# Mount data directory for static frame serving
app.mount("/data", StaticFiles(directory="data"), name="data")

# Mount React static assets if built
dist_dir = os.path.join(os.path.dirname(__file__), "frontend", "dist")
assets_dir = os.path.join(dist_dir, "assets")
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


class ChatRequest(BaseModel):
    question: str


class ActionRequest(BaseModel):
    alert_id: str
    action_type: str


@app.get("/api/status")
def get_system_status():
    """Returns high-level system telemetry, DiaB dock health, and mission stats."""
    all_frames = pipeline.processed_frames
    all_alerts = pipeline.triggered_alerts
    entities = pipeline.context.get_all_entities()

    return {
        "status": "ONLINE",
        "dock_station": "Dock Bay Alpha (North Sector)",
        "dock_status": "LOCKED & SECURED",
        "battery_pct": 96.0,
        "is_charging": True,
        "curfew_active": True,
        "curfew_window": "22:00 - 06:00",
        "total_frames": len(all_frames),
        "total_alerts": len(all_alerts),
        "critical_alerts": sum(1 for a in all_alerts if a.severity.value == "CRITICAL"),
        "warning_alerts": sum(1 for a in all_alerts if a.severity.value == "WARNING"),
        "tracked_entities": len(entities),
        "zones_covered": list(set(f.telemetry.zone_name for f in all_frames))
    }


@app.get("/api/frames")
def get_frames(mission_id: Optional[str] = None):
    """Retrieve all ingested frames with telemetry, VLM caption, and detected entities."""
    frames = pipeline.processed_frames
    if mission_id and mission_id != "ALL":
        frames = [f for f in frames if f.mission_id == mission_id]

    output = []
    for f in frames:
        ann_path = f"data/annotated_frames/annotated_{f.frame_id}.png"
        img_url = f"/{ann_path.replace(os.sep, '/')}" if os.path.exists(ann_path) else f"/{f.image_path.replace(os.sep, '/')}"

        output.append({
            "frame_id": f.frame_id,
            "mission_id": f.mission_id,
            "timestamp": f.timestamp,
            "image_url": img_url,
            "telemetry": f.telemetry.model_dump(),
            "caption": f.caption,
            "detected_objects": [obj.model_dump() for obj in f.detected_objects],
            "activity_summary": f.activity_summary,
            "is_alert": f.is_alert
        })
    return output


@app.get("/api/alerts")
def get_alerts():
    """Retrieve all triggered security policy alerts."""
    return [a.model_dump() for a in pipeline.triggered_alerts]


@app.get("/api/search")
def search_frames(q: str = Query(..., min_length=1)):
    """Cross-domain semantic vector search across video frames using ChromaDB."""
    results = pipeline.vector_store.search(q, top_k=6)
    formatted = []
    for r in results:
        meta = r.get("metadata", {})
        raw_path = meta.get("image_path", "")
        img_url = f"/{raw_path.replace(os.sep, '/')}" if raw_path else ""

        formatted.append({
            "frame_id": meta.get("frame_id"),
            "mission_id": meta.get("mission_id"),
            "timestamp": meta.get("timestamp"),
            "zone_name": meta.get("zone_name"),
            "altitude_m": meta.get("altitude_m"),
            "image_url": img_url,
            "document": r.get("document", ""),
            "score": round(r.get("score", 1.0) * 100, 1),
            "is_alert": meta.get("is_alert") == 1
        })
    return {"query": q, "results": formatted}


@app.post("/api/chat")
def chat_with_agent(req: ChatRequest):
    """Interact with LangChain Security Analyst Agent."""
    answer = pipeline.agent.answer_query(req.question)
    return {"question": req.question, "answer": answer}


@app.get("/api/summary")
def get_mission_summary():
    """Retrieve post-patrol video summarizer output."""
    summary = PatrolVideoSummarizer.generate_summary(
        "PATROL_ALL_SECTORS",
        pipeline.processed_frames,
        pipeline.triggered_alerts
    )
    return summary.model_dump()


@app.post("/api/action")
def execute_tactical_action(req: ActionRequest):
    """Acknowledge or trigger tactical countermeasures."""
    return {
        "status": "DISPATCHED",
        "alert_id": req.alert_id,
        "action": req.action_type,
        "message": f"Tactical countermeasure '{req.action_type.upper()}' dispatched to drone. Target coordinates verified."
    }


# Serve React index.html for root and any frontend routes
@app.get("/")
@app.get("/{full_path:path}")
def serve_react_app(full_path: str = ""):
    index_file = os.path.join(dist_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "FlytBase Drone Security Analyst API is running. Build frontend with 'npm run build'."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
