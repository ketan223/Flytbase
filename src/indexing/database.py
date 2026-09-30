"""
Relational Database for Drone Missions, Telemetry, Frame Detections, and Security Alerts.
Uses SQLite for persistent, zero-dependency structured storage.
"""

import sqlite3
import json
import os
from typing import List, Dict, Any, Optional
from ..telemetry.models import FrameAnalysis, SecurityAlert, DroneTelemetry, DetectedObject


class SecurityDatabase:
    """Manages relational persistence of drone surveillance telemetry, frames, and alerts."""

    def __init__(self, db_path: str = "data/drone_security.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Create structured relational schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Missions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS missions (
                    mission_id TEXT PRIMARY KEY,
                    start_time TEXT,
                    end_time TEXT,
                    status TEXT DEFAULT 'COMPLETED',
                    one_sentence_summary TEXT,
                    executive_summary TEXT
                )
            """)

            # Frames table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS frames (
                    frame_id TEXT PRIMARY KEY,
                    mission_id TEXT,
                    timestamp TEXT,
                    image_path TEXT,
                    altitude_m REAL,
                    latitude REAL,
                    longitude REAL,
                    zone_id TEXT,
                    zone_name TEXT,
                    caption TEXT,
                    activity_summary TEXT,
                    is_alert INTEGER DEFAULT 0,
                    FOREIGN KEY(mission_id) REFERENCES missions(mission_id)
                )
            """)

            # Detected objects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detected_objects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    frame_id TEXT,
                    object_id TEXT,
                    label TEXT,
                    description TEXT,
                    confidence REAL,
                    attributes_json TEXT,
                    bbox_json TEXT,
                    FOREIGN KEY(frame_id) REFERENCES frames(frame_id)
                )
            """)

            # Security alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    alert_id TEXT PRIMARY KEY,
                    mission_id TEXT,
                    frame_id TEXT,
                    timestamp TEXT,
                    severity TEXT,
                    rule_name TEXT,
                    zone_name TEXT,
                    description TEXT,
                    context_reason TEXT,
                    suggested_action TEXT,
                    FOREIGN KEY(frame_id) REFERENCES frames(frame_id)
                )
            """)

            # Create indices for high-performance queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_frames_time ON frames(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_frames_zone ON frames(zone_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_objects_label ON detected_objects(label)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity)")
            conn.commit()

    def insert_frame(self, frame: FrameAnalysis):
        """Insert a frame and its associated detections into SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO frames (
                    frame_id, mission_id, timestamp, image_path,
                    altitude_m, latitude, longitude, zone_id, zone_name,
                    caption, activity_summary, is_alert
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                frame.frame_id,
                frame.mission_id,
                frame.timestamp,
                frame.image_path,
                frame.telemetry.altitude_m,
                frame.telemetry.latitude,
                frame.telemetry.longitude,
                frame.telemetry.zone_id,
                frame.telemetry.zone_name,
                frame.caption,
                frame.activity_summary,
                1 if frame.is_alert else 0
            ))

            for obj in frame.detected_objects:
                cursor.execute("""
                    INSERT INTO detected_objects (
                        frame_id, object_id, label, description,
                        confidence, attributes_json, bbox_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    frame.frame_id,
                    obj.object_id,
                    obj.label,
                    obj.description,
                    obj.confidence,
                    json.dumps(obj.attributes),
                    json.dumps(obj.bbox) if obj.bbox else None
                ))
            conn.commit()

    def insert_alert(self, alert: SecurityAlert):
        """Insert a generated security alert."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO alerts (
                    alert_id, mission_id, frame_id, timestamp,
                    severity, rule_name, zone_name, description,
                    context_reason, suggested_action
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.alert_id,
                alert.mission_id,
                alert.frame_id,
                alert.timestamp,
                alert.severity.value,
                alert.rule_name,
                alert.zone_name,
                alert.description,
                alert.context_reason,
                alert.suggested_action
            ))
            conn.commit()

    def query_by_object(self, term: str) -> List[Dict[str, Any]]:
        """Query frames containing a specific object (e.g., 'truck', 'Ford', 'person')."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT f.*, o.description as detected_desc, o.confidence
                FROM frames f
                JOIN detected_objects o ON f.frame_id = o.frame_id
                WHERE LOWER(o.label) LIKE ? OR LOWER(o.description) LIKE ? OR LOWER(f.caption) LIKE ?
                ORDER BY f.timestamp ASC
            """, (f"%{term.lower()}%", f"%{term.lower()}%", f"%{term.lower()}%"))
            return [dict(row) for row in cursor.fetchall()]

    def query_by_time_range(self, start_time: str, end_time: str) -> List[Dict[str, Any]]:
        """Query frames captured within a specific time window."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM frames
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp ASC
            """, (start_time, end_time))
            return [dict(row) for row in cursor.fetchall()]

    def get_all_alerts(self, min_severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve all logged security alerts."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if min_severity:
                cursor.execute("SELECT * FROM alerts WHERE severity = ? ORDER BY timestamp DESC", (min_severity,))
            else:
                cursor.execute("SELECT * FROM alerts ORDER BY timestamp DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_all_frames(self) -> List[Dict[str, Any]]:
        """Retrieve all stored frames."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM frames ORDER BY timestamp ASC")
            return [dict(row) for row in cursor.fetchall()]
