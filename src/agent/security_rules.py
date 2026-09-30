"""
Security Rules and Alert Evaluation Engine.
Evaluates synchronized telemetry and VLM detections against security policies and historical context.
Produces immediate alerts (e.g., 'Person loitering at main gate, 00:01').
"""

import uuid
from datetime import datetime
from typing import List, Optional
from ..telemetry.models import FrameAnalysis, SecurityAlert, AlertSeverity, DetectedObject
from .context_manager import ContextManager


class SecurityRuleEngine:
    """Evaluates configurable security policies using real-time observations and temporal context."""

    def __init__(self, context_manager: ContextManager, curfew_start: int = 22, curfew_end: int = 6):
        self.context = context_manager
        self.curfew_start = curfew_start  # 22:00 (10 PM)
        self.curfew_end = curfew_end      # 06:00 (6 AM)
        self.loitering_threshold_sec = 20.0  # seconds

    def _is_curfew_hours(self, ts_str: str) -> bool:
        """Check if timestamp falls into restricted night curfew window."""
        try:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%H:%M:%S"):
                try:
                    dt = datetime.strptime(ts_str, fmt)
                    hour = dt.hour
                    return hour >= self.curfew_start or hour < self.curfew_end
                except ValueError:
                    pass
        except Exception:
            pass
        return False

    def evaluate_frame(self, frame: FrameAnalysis) -> List[SecurityAlert]:
        """
        Evaluate all active security rules for a given frame and context.
        Returns a list of triggered SecurityAlert objects.
        """
        alerts: List[SecurityAlert] = []
        is_curfew = self._is_curfew_hours(frame.timestamp)
        zone_lower = frame.telemetry.zone_name.lower()

        for obj in frame.detected_objects:
            dwell_time = self.context.get_active_dwell_time(obj)
            visits = self.context.get_visit_count(obj)

            # -------------------------------------------------------------
            # RULE 1: Person Loitering at Gate / Restricted Area
            # -------------------------------------------------------------
            if obj.label == "person":
                is_loitering_action = "loiter" in obj.attributes.get("action", "").lower()
                is_dwelling = dwell_time >= self.loitering_threshold_sec

                if is_dwelling or is_loitering_action:
                    time_short = frame.timestamp.split()[1][:5] if " " in frame.timestamp else "00:01"
                    alerts.append(
                        SecurityAlert(
                            alert_id=f"ALT_{uuid.uuid4().hex[:8].upper()}",
                            mission_id=frame.mission_id,
                            frame_id=frame.frame_id,
                            timestamp=frame.timestamp,
                            severity=AlertSeverity.CRITICAL if is_curfew else AlertSeverity.WARNING,
                            rule_name="RULE_LOITERING_DETECTED",
                            zone_name=frame.telemetry.zone_name,
                            description=f"Person loitering at {frame.telemetry.zone_name.lower()}, {time_short}.",
                            context_reason=(
                                f"Subject identified stationary in {frame.telemetry.zone_name} for "
                                f"{dwell_time:.1f}s during {'curfew hours' if is_curfew else 'daylight patrol'}."
                            ),
                            suggested_action="Dispatch perimeter patrol unit to issue verbal dispersal warning via drone loudspeaker."
                        )
                    )

                # Curfew trespass rule
                elif is_curfew:
                    alerts.append(
                        SecurityAlert(
                            alert_id=f"ALT_{uuid.uuid4().hex[:8].upper()}",
                            mission_id=frame.mission_id,
                            frame_id=frame.frame_id,
                            timestamp=frame.timestamp,
                            severity=AlertSeverity.CRITICAL,
                            rule_name="RULE_CURFEW_TRESPASS",
                            zone_name=frame.telemetry.zone_name,
                            description=f"Unauthorized pedestrian activity in {frame.telemetry.zone_name} during curfew.",
                            context_reason=f"Individual detected at {frame.timestamp} during restricted operational hours.",
                            suggested_action="Engage drone spotlight and alert property monitoring dispatch."
                        )
                    )

            # -------------------------------------------------------------
            # RULE 2: Repeat Vehicle Visit ("Blue Ford F150 entered twice today")
            # -------------------------------------------------------------
            if obj.label == "vehicle" and visits >= 2:
                alerts.append(
                    SecurityAlert(
                        alert_id=f"ALT_{uuid.uuid4().hex[:8].upper()}",
                        mission_id=frame.mission_id,
                        frame_id=frame.frame_id,
                        timestamp=frame.timestamp,
                        severity=AlertSeverity.WARNING,
                        rule_name="RULE_REPEAT_VEHICLE_ENTRY",
                        zone_name=frame.telemetry.zone_name,
                        description=f"{obj.description} entered twice today.",
                        context_reason=(
                            f"Vehicle {obj.description} has re-entered property grounds (visit #{visits}). "
                            f"Previous sighting was logged earlier today."
                        ),
                        suggested_action="Cross-reference gate visitor pass log for authorized multi-entry access."
                    )
                )

            # -------------------------------------------------------------
            # RULE 3: Unauthorized After-Hours Vehicle Activity
            # -------------------------------------------------------------
            if obj.label == "vehicle" and is_curfew:
                alerts.append(
                    SecurityAlert(
                        alert_id=f"ALT_{uuid.uuid4().hex[:8].upper()}",
                        mission_id=frame.mission_id,
                        frame_id=frame.frame_id,
                        timestamp=frame.timestamp,
                        severity=AlertSeverity.WARNING,
                        rule_name="RULE_AFTER_HOURS_VEHICLE",
                        zone_name=frame.telemetry.zone_name,
                        description=f"Vehicle detected operating in {frame.telemetry.zone_name} during curfew window.",
                        context_reason=f"Vehicle {obj.description} observed active at {frame.timestamp}.",
                        suggested_action="Verify if delivery or commercial contractor has approved night-access permit."
                    )
                )

            # -------------------------------------------------------------
            # RULE 4: Fire Lane & Emergency Obstruction
            # -------------------------------------------------------------
            if "fire" in zone_lower or "emergency" in zone_lower:
                alerts.append(
                    SecurityAlert(
                        alert_id=f"ALT_{uuid.uuid4().hex[:8].upper()}",
                        mission_id=frame.mission_id,
                        frame_id=frame.frame_id,
                        timestamp=frame.timestamp,
                        severity=AlertSeverity.CRITICAL,
                        rule_name="RULE_EMERGENCY_LANE_OBSTRUCTION",
                        zone_name=frame.telemetry.zone_name,
                        description=f"Obstruction hazard: {obj.description} stationed inside designated fire lane.",
                        context_reason="Emergency egress zone must remain clear of all vehicular traffic at all times.",
                        suggested_action="Order immediate vehicle relocation."
                    )
                )

        if alerts:
            frame.is_alert = True

        return alerts
