"""
Drone Mission and Telemetry Stream Simulator.
Simulates a docked autonomous drone executing surveillance patrols over industrial properties.
"""

import json
import time
from typing import Iterator, List, Optional
from .models import DroneTelemetry, FrameAnalysis, DetectedObject


class DroneMissionSimulator:
    """Streams synchronized telemetry and visual frames for autonomous patrol missions."""

    def __init__(self, flight_log_path: str = "data/sample_flight_logs.json"):
        self.flight_log_path = flight_log_path
        self._frames_cache: List[dict] = []
        self._load_flight_logs()

    def _load_flight_logs(self):
        with open(self.flight_log_path, "r") as f:
            self._frames_cache = json.load(f)

    def get_all_missions(self) -> List[str]:
        """List distinct mission IDs available in the simulator."""
        return sorted(list(set(item["mission_id"] for item in self._frames_cache)))

    def stream_mission(self, mission_id: Optional[str] = None, interval_sec: float = 0.0) -> Iterator[FrameAnalysis]:
        """
        Stream frames for a specified mission (or all missions if None).
        Optional interval_sec simulates real-time drone telemetry broadcast.
        """
        for item in self._frames_cache:
            if mission_id and item["mission_id"] != mission_id:
                continue

            telemetry_data = DroneTelemetry(**item["telemetry"])
            detected_objs = [
                DetectedObject(
                    object_id=obj["object_id"],
                    label=obj["label"],
                    description=obj["description"],
                    attributes=obj.get("attributes", {}),
                    confidence=obj.get("confidence", 0.95),
                    bbox=obj.get("bbox")
                )
                for obj in item.get("objects", [])
            ]

            frame_analysis = FrameAnalysis(
                frame_id=item["frame_id"],
                mission_id=item["mission_id"],
                timestamp=item["timestamp"],
                image_path=item["image_path"],
                telemetry=telemetry_data,
                caption=item["caption"],
                detected_objects=detected_objs,
                activity_summary=item["activity_summary"],
                is_alert=False
            )

            if interval_sec > 0:
                time.sleep(interval_sec)

            yield frame_analysis
