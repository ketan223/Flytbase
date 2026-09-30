"""
Tests for Context Management and Security Rules Engine.
Explicitly verifies assignment requirements:
1. 'Truck logged correctly' ('Blue Ford F150 spotted at garage, 12:00')
2. 'Alert triggered at midnight' ('Person loitering at main gate, 00:01')
3. Cross-frame memory: 'a blue Ford F150 entered twice today'
"""

import pytest
from src.telemetry.models import DroneTelemetry, FrameAnalysis, DetectedObject, AlertSeverity
from src.agent.context_manager import ContextManager
from src.agent.security_rules import SecurityRuleEngine


@pytest.fixture
def context_and_rules():
    ctx = ContextManager()
    rules = SecurityRuleEngine(context_manager=ctx)
    return ctx, rules


def test_truck_logged_correctly(context_and_rules):
    """Verify that a vehicle is correctly logged with context and timestamp."""
    ctx, rules = context_and_rules

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
        attributes={"color": "blue", "make": "Ford", "model": "F150"}
    )

    frame = FrameAnalysis(
        frame_id="F_TEST_01",
        mission_id="DAY_01",
        timestamp="2026-09-30 12:00:00",
        image_path="data/frames/FRAME_002.png",
        telemetry=telemetry,
        caption="Blue Ford F150 spotted at garage, 12:00.",
        detected_objects=[obj],
        activity_summary="Vehicle parking at garage."
    )

    logs = ctx.process_frame(frame)
    assert len(logs) > 0
    assert "Blue Ford F150 spotted at garage, 12:00." in logs[0]

    # Check entity was stored in context memory
    entity = ctx.get_entity("Ford")
    assert entity is not None
    assert entity.sighting_count == 1
    assert entity.distinct_visits == 1


def test_alert_triggered_at_midnight(context_and_rules):
    """Verify that a person loitering at midnight triggers an immediate critical alert."""
    ctx, rules = context_and_rules

    telemetry = DroneTelemetry(
        timestamp="2026-09-30 00:01:00",
        latitude=37.7749,
        longitude=-122.4194,
        altitude_m=14.0,
        battery_pct=98.0,
        zone_id="ZONE_GATE",
        zone_name="Main Gate",
        mission_id="NIGHT_01"
    )

    person = DetectedObject(
        object_id="PER_001",
        label="person",
        description="Individual in dark hoodie",
        attributes={"clothing": "dark hoodie", "action": "loitering"}
    )

    frame = FrameAnalysis(
        frame_id="F_TEST_02",
        mission_id="NIGHT_01",
        timestamp="2026-09-30 00:01:00",
        image_path="data/frames/FRAME_005.png",
        telemetry=telemetry,
        caption="Person loitering at main gate, 00:01.",
        detected_objects=[person],
        activity_summary="Subject standing stationary at gate."
    )

    ctx.process_frame(frame)
    alerts = rules.evaluate_frame(frame)

    assert len(alerts) >= 1
    loitering_alert = next((a for a in alerts if "loitering" in a.description.lower()), None)
    assert loitering_alert is not None
    assert loitering_alert.severity == AlertSeverity.CRITICAL
    assert "Main Gate" in loitering_alert.zone_name
    assert "00:01" in loitering_alert.description


def test_repeat_vehicle_entry_tracking(context_and_rules):
    """Verify that when a vehicle enters twice today, recurrence memory detects it and triggers an alert."""
    ctx, rules = context_and_rules

    # First entry at noon
    t1 = DroneTelemetry(
        timestamp="2026-09-30 12:00:00",
        latitude=37.7749,
        longitude=-122.4194,
        altitude_m=16.0,
        battery_pct=99.0,
        zone_id="ZONE_GATE",
        zone_name="Main Gate",
        mission_id="DAY_01"
    )
    v1 = DetectedObject(
        object_id="VEH_001",
        label="vehicle",
        description="Blue Ford F150",
        attributes={"make": "Ford", "model": "F150", "color": "blue"}
    )
    f1 = FrameAnalysis(
        frame_id="F1",
        timestamp="2026-09-30 12:00:00",
        image_path="dummy.png",
        telemetry=t1,
        caption="Blue Ford F150 at gate.",
        detected_objects=[v1],
        activity_summary="Entry."
    )
    ctx.process_frame(f1)
    alerts1 = rules.evaluate_frame(f1)
    # First time: no repeat alert
    assert not any(a.rule_name == "RULE_REPEAT_VEHICLE_ENTRY" for a in alerts1)

    # Second entry at midnight (repeat visit)
    t2 = DroneTelemetry(
        timestamp="2026-09-30 00:02:15",
        latitude=37.7761,
        longitude=-122.4178,
        altitude_m=15.0,
        battery_pct=95.0,
        zone_id="ZONE_WAREHOUSE",
        zone_name="Warehouse Loading Bay",
        mission_id="NIGHT_01"
    )
    f2 = FrameAnalysis(
        frame_id="F2",
        timestamp="2026-09-30 00:02:15",
        image_path="dummy.png",
        telemetry=t2,
        caption="Blue Ford F150 at warehouse.",
        detected_objects=[v1],
        activity_summary="Second entry."
    )
    ctx.process_frame(f2)
    alerts2 = rules.evaluate_frame(f2)

    # Must trigger repeat vehicle alert!
    repeat_alert = next((a for a in alerts2 if a.rule_name == "RULE_REPEAT_VEHICLE_ENTRY"), None)
    assert repeat_alert is not None
    assert "Blue Ford F150 entered twice today." in repeat_alert.description
