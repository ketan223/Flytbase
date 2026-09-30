"""
Tests for Bonus Enhancements:
1. Video Summarization (1-sentence summary and executive debrief)
2. LangChain Conversational Security Analyst Agent (follow-up Q&A capability)
"""

import pytest
from src.telemetry.models import DroneTelemetry, FrameAnalysis, DetectedObject, SecurityAlert, AlertSeverity
from src.agent.summarizer import PatrolVideoSummarizer
from src.agent.context_manager import ContextManager
from src.agent.langchain_agent import DroneSecurityAnalystAgent
from src.indexing.database import SecurityDatabase
from src.indexing.vector_store import FrameVectorStore


def test_video_summarizer_bonus():
    """Verify 1-sentence video summary and executive debrief generation."""
    telemetry = DroneTelemetry(
        timestamp="2026-09-30 00:01:00",
        latitude=37.7749,
        longitude=-122.4194,
        altitude_m=14.0,
        battery_pct=98.0,
        zone_id="ZONE_GATE",
        zone_name="Main Gate",
        mission_id="PATROL_NIGHT_001"
    )

    frame = FrameAnalysis(
        frame_id="F_NIGHT_01",
        mission_id="PATROL_NIGHT_001",
        timestamp="2026-09-30 00:01:00",
        image_path="test.png",
        telemetry=telemetry,
        caption="Person loitering at main gate, 00:01.",
        detected_objects=[DetectedObject(object_id="P1", label="person", description="Individual in dark hoodie")],
        activity_summary="Subject standing stationary."
    )

    alert = SecurityAlert(
        alert_id="ALT_001",
        mission_id="PATROL_NIGHT_001",
        frame_id="F_NIGHT_01",
        timestamp="2026-09-30 00:01:00",
        severity=AlertSeverity.CRITICAL,
        rule_name="RULE_LOITERING_DETECTED",
        zone_name="Main Gate",
        description="Person loitering at main gate, 00:01.",
        context_reason="Stationary human after hours.",
        suggested_action="Dispatch guard."
    )

    summary = PatrolVideoSummarizer.generate_summary(
        mission_id="PATROL_NIGHT_001",
        frames=[frame],
        alerts=[alert]
    )

    # 1-Sentence summary validation
    assert summary.one_sentence_summary is not None
    assert "PATROL_NIGHT_001" in summary.one_sentence_summary
    assert "Person loitering at main gate, 00:01." in summary.one_sentence_summary

    # Executive debrief validation
    assert "AUTONOMOUS DRONE PATROL DEBRIEF" in summary.executive_summary
    assert summary.total_alerts == 1
    assert summary.alerts_by_severity["CRITICAL"] == 1


def test_agent_follow_up_qa_bonus(tmp_path):
    """Verify agent capability to answer follow-up questions."""
    db_file = str(tmp_path / "qa_sec.db")
    chroma_dir = str(tmp_path / "qa_chroma")

    db = SecurityDatabase(db_path=db_file)
    vs = FrameVectorStore(persist_dir=chroma_dir)
    ctx = ContextManager()

    agent = DroneSecurityAnalystAgent(vector_store=vs, database=db, context_manager=ctx)

    telemetry = DroneTelemetry(
        timestamp="2026-09-30 12:00:00",
        latitude=37.7753,
        longitude=-122.4188,
        altitude_m=18.0,
        battery_pct=96.0,
        zone_id="ZONE_GARAGE",
        zone_name="Garage",
        mission_id="DAY_01"
    )

    obj = DetectedObject(
        object_id="VEH_001",
        label="vehicle",
        description="Blue Ford F150",
        attributes={"color": "blue"}
    )

    frame = FrameAnalysis(
        frame_id="F_QA_01",
        mission_id="DAY_01",
        timestamp="2026-09-30 12:00:00",
        image_path="test.png",
        telemetry=telemetry,
        caption="Blue Ford F150 spotted at garage, 12:00.",
        detected_objects=[obj],
        activity_summary="Parking."
    )

    ctx.process_frame(frame)
    db.insert_frame(frame)
    vs.index_frame(frame)

    # Question 1: What objects were in the video?
    ans1 = agent.answer_query("What objects were in the video?")
    assert "Blue Ford F150" in ans1 or "vehicle" in ans1

    # Question 2: Did the blue Ford F150 visit today?
    ans2 = agent.answer_query("How many times was the blue Ford F150 seen today?")
    assert "Blue Ford F150" in ans2
    assert "Visited 1 time" in ans2 or "1" in ans2
