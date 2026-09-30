"""
Tests for Cross-Domain Frame Indexing and Search.
Verifies relational database storage (SQLite) and semantic vector search (ChromaDB).
Tests query requirement: 'show all truck events'.
"""

import pytest
import shutil
import os
from src.telemetry.models import DroneTelemetry, FrameAnalysis, DetectedObject
from src.indexing.database import SecurityDatabase
from src.indexing.vector_store import FrameVectorStore


@pytest.fixture
def temp_stores(tmp_path):
    db_file = str(tmp_path / "test_sec.db")
    chroma_dir = str(tmp_path / "test_chroma")
    
    db = SecurityDatabase(db_path=db_file)
    vs = FrameVectorStore(persist_dir=chroma_dir)
    return db, vs


def test_sqlite_indexing_and_query(temp_stores):
    """Verify frames and objects can be stored and retrieved from SQLite."""
    db, _ = temp_stores

    telemetry = DroneTelemetry(
        timestamp="2026-09-30 12:00:00",
        latitude=37.7753,
        longitude=-122.4188,
        altitude_m=18.0,
        battery_pct=96.0,
        zone_id="ZONE_GARAGE",
        zone_name="Garage",
        mission_id="TEST_M"
    )

    obj = DetectedObject(
        object_id="VEH_001",
        label="vehicle",
        description="Blue Ford F150",
        attributes={"color": "blue"}
    )

    frame = FrameAnalysis(
        frame_id="F_TEST_100",
        mission_id="TEST_M",
        timestamp="2026-09-30 12:00:00",
        image_path="test.png",
        telemetry=telemetry,
        caption="Blue Ford F150 spotted at garage, 12:00.",
        detected_objects=[obj],
        activity_summary="Parking."
    )

    db.insert_frame(frame)

    # Query by object
    results = db.query_by_object("truck") + db.query_by_object("Ford")
    assert len(results) > 0
    assert results[0]["frame_id"] == "F_TEST_100"


def test_chroma_semantic_search_truck_events(temp_stores):
    """Verify semantic vector search handles 'show all truck events'."""
    _, vs = temp_stores

    telemetry_truck = DroneTelemetry(
        timestamp="2026-09-30 12:00:00",
        latitude=37.7753,
        longitude=-122.4188,
        altitude_m=18.0,
        battery_pct=96.0,
        zone_id="ZONE_GARAGE",
        zone_name="Executive Garage",
        mission_id="TEST_M"
    )

    truck_obj = DetectedObject(
        object_id="VEH_TRUCK",
        label="vehicle",
        description="Blue Ford F150 pickup truck"
    )

    truck_frame = FrameAnalysis(
        frame_id="FRAME_TRUCK_01",
        mission_id="TEST_M",
        timestamp="2026-09-30 12:00:00",
        image_path="test_truck.png",
        telemetry=telemetry_truck,
        caption="Blue Ford F150 pickup truck spotted at garage, 12:00.",
        detected_objects=[truck_obj],
        activity_summary="Truck parked outside garage bay."
    )

    vs.index_frame(truck_frame)

    # Execute search for 'show all truck events'
    query_results = vs.search("show all truck events", top_k=1)
    assert len(query_results) >= 1
    top_match = query_results[0]
    assert top_match["frame_id"] == "FRAME_TRUCK_01"
    assert "truck" in top_match["document"].lower() or "ford" in top_match["document"].lower()
