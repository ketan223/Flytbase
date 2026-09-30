"""
Tests for Drone Telemetry Ingestion and Simulator.
Verifies telemetry schemas, GPS coordinate bounds, and mission streaming.
"""

import pytest
from src.telemetry.models import DroneTelemetry, DetectedObject
from src.telemetry.drone_simulator import DroneMissionSimulator


def test_drone_telemetry_model():
    """Verify DroneTelemetry schema parsing and validation."""
    telemetry = DroneTelemetry(
        timestamp="2026-09-30 12:00:00",
        latitude=37.7749,
        longitude=-122.4194,
        altitude_m=15.5,
        battery_pct=95.0,
        speed_mps=3.2,
        heading_deg=180.0,
        zone_id="ZONE_GATE",
        zone_name="Main Gate",
        mission_id="TEST_MISSION_01"
    )

    assert telemetry.zone_name == "Main Gate"
    assert telemetry.altitude_m == 15.5
    assert 0 <= telemetry.battery_pct <= 100
    assert -90 <= telemetry.latitude <= 90
    assert -180 <= telemetry.longitude <= 180


def test_drone_simulator_stream():
    """Verify simulator properly loads and streams frames."""
    sim = DroneMissionSimulator(flight_log_path="data/sample_flight_logs.json")
    missions = sim.get_all_missions()
    assert len(missions) >= 2
    assert "PATROL_DAY_1200" in missions
    assert "PATROL_NIGHT_0001" in missions

    frames = list(sim.stream_mission("PATROL_DAY_1200"))
    assert len(frames) == 3
    assert frames[0].frame_id == "FRAME_001"
    assert frames[0].telemetry.zone_name == "Main Gate"
