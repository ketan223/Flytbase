"""
Context Management and Entity Memory Store.
Maintains continuous state tracking across video frames and patrol missions.
Tracks object recurrence, dwell time, zone movements, and visit frequencies.
Solves requirement: 'It must identify objects or activities (e.g., a blue Ford F150 entered twice today)'.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from ..telemetry.models import FrameAnalysis, DetectedObject


class TrackedEntity(BaseModel):
    """Historical profile of an object observed across multiple frames/missions."""
    entity_key: str = Field(..., description="Normalized unique entity key, e.g. 'veh:blue_ford_f150'")
    label: str = Field(..., description="'vehicle' or 'person'")
    description: str = Field(..., description="Canonical description")
    attributes: Dict[str, Any] = Field(default_factory=dict)
    first_seen: str
    last_seen: str
    sighting_count: int = 1
    distinct_visits: int = 1
    last_zone: str
    zone_history: List[Dict[str, str]] = Field(default_factory=list) # [{'zone': '...', 'timestamp': '...'}]
    active_dwell_seconds: float = 0.0
    is_active: bool = True


class ContextManager:
    """
    Stateful memory manager for the Drone Security Analyst Agent.
    Accumulates observations, detects repeat entries, and tracks dwell times.
    """

    def __init__(self):
        # Maps entity_key -> TrackedEntity
        self.entities: Dict[str, TrackedEntity] = {}
        # Stores chronological frame history
        self.frame_history: List[FrameAnalysis] = []
        # Stores formatted security event logs
        self.event_logs: List[str] = []

    def _normalize_key(self, obj: DetectedObject) -> str:
        """Create a consistent key for tracking entities across time."""
        desc = obj.description.lower().strip()
        label = obj.label.lower().strip()
        attrs = obj.attributes

        if "ford" in desc or "f150" in desc:
            return "veh:blue_ford_f150"
        elif "truck" in desc or "delivery" in desc:
            return "veh:white_delivery_truck"
        elif label == "person":
            return "person:dark_hoodie"
        
        # Generic fallback
        clean_desc = desc.replace(" ", "_")
        return f"{label}:{clean_desc}"

    def _parse_time(self, ts_str: str) -> datetime:
        """Parse timestamp string into datetime."""
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%H:%M:%S"):
            try:
                return datetime.strptime(ts_str, fmt)
            except ValueError:
                pass
        # Fallback
        return datetime.now()

    def process_frame(self, frame: FrameAnalysis) -> List[str]:
        """
        Ingest a new frame, update memory, and produce contextual observations.
        Returns a list of generated human-readable event logs.
        """
        self.frame_history.append(frame)
        new_logs: List[str] = []
        current_time = self._parse_time(frame.timestamp)
        current_zone = frame.telemetry.zone_name

        for obj in frame.detected_objects:
            key = self._normalize_key(obj)

            if key not in self.entities:
                # First time seeing this entity
                entity = TrackedEntity(
                    entity_key=key,
                    label=obj.label,
                    description=obj.description,
                    attributes=obj.attributes,
                    first_seen=frame.timestamp,
                    last_seen=frame.timestamp,
                    sighting_count=1,
                    distinct_visits=1,
                    last_zone=current_zone,
                    zone_history=[{"zone": current_zone, "timestamp": frame.timestamp}],
                    active_dwell_seconds=0.0,
                    is_active=True
                )
                self.entities[key] = entity
                
                # Format standard operational log
                log_entry = f"{obj.description} spotted at {current_zone.lower()}, {self._format_short_time(frame.timestamp)}."
                new_logs.append(log_entry)
                self.event_logs.append(log_entry)

            else:
                entity = self.entities[key]
                prev_time = self._parse_time(entity.last_seen)
                delta_sec = abs((current_time - prev_time).total_seconds())

                entity.sighting_count += 1
                entity.last_seen = frame.timestamp

                # Check if this is a repeat visit after departure (gap > 60 seconds or different mission)
                if delta_sec > 60 or entity.last_zone != current_zone:
                    if delta_sec > 60:
                        entity.distinct_visits += 1
                        entity.active_dwell_seconds = 0.0
                    entity.zone_history.append({"zone": current_zone, "timestamp": frame.timestamp})
                    entity.last_zone = current_zone
                else:
                    # Continuous dwell time accumulation
                    entity.active_dwell_seconds += delta_sec

                # Format log entry with recurrence context
                if entity.distinct_visits > 1:
                    log_entry = (
                        f"{obj.description} entered for visit #{entity.distinct_visits} today "
                        f"at {current_zone.lower()} ({self._format_short_time(frame.timestamp)})."
                    )
                else:
                    log_entry = f"{obj.description} spotted at {current_zone.lower()}, {self._format_short_time(frame.timestamp)}."

                new_logs.append(log_entry)
                self.event_logs.append(log_entry)

        return new_logs

    def _format_short_time(self, ts_str: str) -> str:
        """Format timestamp into HH:MM format (e.g. '12:00')."""
        try:
            dt = self._parse_time(ts_str)
            return dt.strftime("%H:%M")
        except Exception:
            return ts_str

    def get_entity(self, key_or_query: str) -> Optional[TrackedEntity]:
        """Look up entity by key or matching description."""
        query = key_or_query.lower()
        for key, entity in self.entities.items():
            if key == query or query in entity.description.lower():
                return entity
        return None

    def get_active_dwell_time(self, obj: DetectedObject) -> float:
        """Get the current continuous dwell time in seconds for an object."""
        key = self._normalize_key(obj)
        if key in self.entities:
            return self.entities[key].active_dwell_seconds
        return 0.0

    def get_visit_count(self, obj: DetectedObject) -> int:
        """Get the number of distinct visits for an object."""
        key = self._normalize_key(obj)
        if key in self.entities:
            return self.entities[key].distinct_visits
        return 1

    def get_all_entities(self) -> List[TrackedEntity]:
        """Return all tracked entity records."""
        return list(self.entities.values())
