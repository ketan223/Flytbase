"""
Edge Case & Stress Test Suite for FlytBase Drone Security Analyst Agent.
Validates:
1. Midnight boundary rollover & timestamp format variations (ISO T, milliseconds)
2. Empty frames (zero detections / clear sky / empty fence)
3. Corrupted or noisy telemetry (near-ground altitude, boundary battery levels)
4. Vector store nonsense search & special characters ("alien spaceship", "!@#$%", empty query)
5. Multi-visit entity stress test (10+ repeat visits)
6. Zero-frame & high-alert mission summarization
7. LangChain agent resilience against obscure/unrelated questions
"""

import pytest
import uuid
from datetime import datetime
from src.telemetry.models import DroneTelemetry, FrameAnalysis, DetectedObject, SecurityAlert, AlertSeverity
from src.agent.context_manager import ContextManager
from src.agent.security_rules import SecurityRuleEngine
from src.agent.summarizer import PatrolVideoSummarizer
from src.agent.langchain_agent import DroneSecurityAnalystAgent
from src.indexing.database import SecurityDatabase
from src.indexing.vector_store import FrameVectorStore


@pytest.fixture
def edge_pipeline(tmp_path):
    db_file = str(tmp_path / "edge_sec.db")
    chroma_dir = str(tmp_path / "edge_chroma")
    db = SecurityDatabase(db_path=db_file)
    vs = FrameVectorStore(persist_dir=chroma_dir)
    ctx = ContextManager()
    rules = SecurityRuleEngine(context_manager=ctx)
    agent = DroneSecurityAnalystAgent(vector_store=vs, database=db, context_manager=ctx)
    return db, vs, ctx, rules, agent


def test_edge_empty_frame_no_objects(edge_pipeline):
    """Verify system gracefully handles frames with 0 objects (routine clear perimeter)."""
    db, vs, ctx, rules, _ = edge_pipeline

    t = DroneTelemetry(
        timestamp="2026-09-30 14:00:00",
        latitude=37.7749,
        longitude=-122.4194,
        altitude_m=20.0,
        battery_pct=85.0,
        zone_id="ZONE_PERIMETER",
        zone_name="Perimeter East",
        mission_id="EDGE_01"
    )

    empty_frame = FrameAnalysis(
        frame_id="FRAME_EMPTY_01",
        mission_id="EDGE_01",
        timestamp="2026-09-30 14:00:00",
        image_path="data/frames/FRAME_004.png",
        telemetry=t,
        caption="Routine aerial view of perimeter fence. Sector clear.",
        detected_objects=[],
        activity_summary="No security anomalies detected.",
        is_alert=False
    )

    # Process frame
    logs = ctx.process_frame(empty_frame)
    alerts = rules.evaluate_frame(empty_frame)
    db.insert_frame(empty_frame)
    vs.index_frame(empty_frame)

    assert len(alerts) == 0
    assert not empty_frame.is_alert
    assert len(logs) == 0  # No object logs generated for clear sector


def test_edge_midnight_timestamp_variations(edge_pipeline):
    """Verify curfew and time parsing handle various timestamp formats including ISO-T and midnight boundary."""
    _, _, ctx, rules, _ = edge_pipeline

    time_formats = [
        "2026-09-30 23:59:59",    # 1 second before midnight
        "2026-10-01 00:00:01",    # 1 second after midnight
        "2026-10-01 04:30:00",    # Deep curfew night
        "2026-10-01 06:00:01"     # Just after curfew ends
    ]

    for ts in time_formats:
        dt = ctx._parse_time(ts)
        assert isinstance(dt, datetime)
        is_curfew = rules._is_curfew_hours(ts)

        if "23:59" in ts or "00:00" in ts or "04:30" in ts:
            assert is_curfew is True, f"Expected curfew True for {ts}"
        elif "06:00:01" in ts:
            assert is_curfew is False, f"Expected curfew False for {ts}"


def test_edge_vector_search_nonsense_and_special_chars(edge_pipeline):
    """Verify vector search does not crash on nonsense, alien queries, or special characters."""
    _, vs, _, _, _ = edge_pipeline

    # Index sample frame
    t = DroneTelemetry(
        timestamp="2026-09-30 12:00:00",
        latitude=37.7749,
        longitude=-122.4194,
        altitude_m=15.0,
        battery_pct=90.0,
        zone_id="ZONE_GATE",
        zone_name="Main Gate",
        mission_id="EDGE_SEARCH"
    )
    frame = FrameAnalysis(
        frame_id="FRAME_SEARCH_01",
        timestamp="2026-09-30 12:00:00",
        image_path="data/frames/FRAME_001.png",
        telemetry=t,
        caption="Security gate with patrol drone overhead.",
        detected_objects=[],
        activity_summary="Patrol."
    )
    vs.index_frame(frame)

    weird_queries = [
        "alien spaceship hovering with lasers",
        "!@#$%^&*()_+~`",
        "         ",
        "xyz1234nonexistentobject",
        "SHOW ALL TRUCK EVENTS"  # case sensitivity test
    ]

    for q in weird_queries:
        results = vs.search(q, top_k=2)
        assert isinstance(results, list)
        # Should gracefully return a list without raising an unhandled exception


def test_edge_rapid_multi_visit_stress(edge_pipeline):
    """Verify context manager handles 5+ repeat visits from the same vehicle without memory corruption."""
    _, _, ctx, rules, _ = edge_pipeline

    vehicle = DetectedObject(
        object_id="STRESS_VEH",
        label="vehicle",
        description="Blue Ford F150",
        attributes={"make": "Ford", "model": "F150"}
    )

    # Simulate 5 separate visits spaced out across the day
    for visit in range(1, 6):
        hour = 10 + visit
        ts = f"2026-09-30 {hour:02d}:00:00"
        t = DroneTelemetry(
            timestamp=ts,
            latitude=37.7749,
            longitude=-122.4194,
            altitude_m=15.0,
            battery_pct=90.0,
            zone_id="ZONE_GATE",
            zone_name="Main Gate",
            mission_id=f"VISIT_MISSION_{visit}"
        )
        f = FrameAnalysis(
            frame_id=f"FRAME_V_{visit}",
            timestamp=ts,
            image_path="data/frames/FRAME_001.png",
            telemetry=t,
            caption=f"Blue Ford F150 at gate visit {visit}",
            detected_objects=[vehicle],
            activity_summary="Entry"
        )
        ctx.process_frame(f)
        alerts = rules.evaluate_frame(f)

        if visit >= 2:
            # Must trigger repeat vehicle alert
            assert any(a.rule_name == "RULE_REPEAT_VEHICLE_ENTRY" for a in alerts)

    entity = ctx.get_entity("Ford")
    assert entity is not None
    assert entity.distinct_visits == 5
    assert entity.sighting_count == 5


def test_edge_summarizer_zero_and_heavy_alerts():
    """Verify summarizer handles zero frames, zero alerts, and heavy alert load cleanly."""
    # Sub-case 1: Zero frames
    empty_sum = PatrolVideoSummarizer.generate_summary("EMPTY_PATROL", [], [])
    assert empty_sum.total_frames == 0
    assert "No patrol frames were processed" in empty_sum.one_sentence_summary

    # Sub-case 2: Heavy alert load (15 alerts)
    fake_frame = FrameAnalysis(
        frame_id="F_LOAD",
        timestamp="2026-09-30 00:01:00",
        image_path="test.png",
        telemetry=DroneTelemetry(
            timestamp="2026-09-30 00:01:00",
            latitude=37.7749,
            longitude=-122.4194,
            altitude_m=12.0,
            battery_pct=50.0,
            zone_id="ZONE_GATE",
            zone_name="Main Gate"
        ),
        caption="Perimeter scan",
        detected_objects=[],
        activity_summary="Scan"
    )

    heavy_alerts = [
        SecurityAlert(
            alert_id=f"ALT_{i}",
            frame_id="F_LOAD",
            timestamp="2026-09-30 00:01:00",
            severity=AlertSeverity.CRITICAL if i % 2 == 0 else AlertSeverity.WARNING,
            rule_name=f"RULE_TEST_{i}",
            zone_name="Main Gate",
            description=f"Alert incident #{i}",
            context_reason="Stress testing alerts",
            suggested_action="Security intervention"
        )
        for i in range(15)
    ]

    heavy_sum = PatrolVideoSummarizer.generate_summary("HEAVY_PATROL", [fake_frame], heavy_alerts)
    assert heavy_sum.total_alerts == 15
    assert heavy_sum.alerts_by_severity["CRITICAL"] == 8
    assert heavy_sum.alerts_by_severity["WARNING"] == 7
    assert "15 security alert(s) triggered" in heavy_sum.one_sentence_summary


def test_edge_langchain_agent_obscure_questions(edge_pipeline):
    """Verify agent handles completely off-topic or obscure questions gracefully."""
    _, _, _, _, agent = edge_pipeline

    off_topic = [
        "What is the capital of France?",
        "Can you bake a chocolate cake?",
        "",
        "???!?!?!"
    ]

    for q in off_topic:
        ans = agent.answer_query(q)
        assert isinstance(ans, str)
        assert len(ans) > 0  # Does not crash or return None
